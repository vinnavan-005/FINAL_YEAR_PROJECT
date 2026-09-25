import math
from collections import deque
from enum import Enum
import numpy as np
import pandas as pd

class ObjectVisibilityState(Enum):
    """Discrete state machine representing physical object persistence."""
    VISIBLE = "VISIBLE"               # Actively detected by sensor/vision model
    OCCLUDED = "OCCLUDED"             # Missing from sensory view, but predicted within frame bounds
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"   # Extrapolated trajectory has exited frame boundaries
    LOST = "LOST"                     # Exceeded maximum temporal memory retention threshold

class MemoryTrackSlot:
    """
    Maintains persistent kinematic state, trajectory buffer, and ballistic prediction
    for a single tracked physical entity.
    """

    def __init__(
        self,
        track_id: int,
        class_name: str,
        initial_box: tuple,
        confidence: float,
        frame_idx: int,
        history_len: int = 30
    ):
        self.track_id = track_id
        self.class_name = class_name
        self.state = ObjectVisibilityState.VISIBLE
        
        # Kinematic history buffers
        self.history_centroids = deque(maxlen=history_len)
        self.history_boxes = deque(maxlen=history_len)
        self.history_areas = deque(maxlen=history_len)
        self.history_frames = deque(maxlen=history_len)
        
        # Motion vectors (pixels / frame)
        self.velocity = np.zeros(2, dtype=np.float32)  # [vx, vy]
        self.acceleration = np.zeros(2, dtype=np.float32)  # [ax, ay]
        
        # Ballistic predictions during occlusion
        self.predicted_centroid = None  # (pred_x, pred_y)
        self.predicted_box = None       # (pred_x1, pred_y1, pred_x2, pred_y2)
        
        # Counters and lifetime metrics
        self.first_seen_frame = frame_idx
        self.last_seen_frame = frame_idx
        self.frames_visible = 0
        self.frames_occluded = 0
        self.total_occlusion_episodes = 0
        self.confidence_decay = float(confidence)
        
        # Initialize with first detection
        self.update_visible(frame_idx, initial_box, confidence, class_name)

    def update_visible(self, frame_idx: int, box: tuple, confidence: float, class_name: str = None):
        """Updates slot with active sensory detection."""
        if class_name:
            self.class_name = class_name
            
        x1, y1, x2, y2 = box
        w = max(float(x2 - x1), 1.0)
        h = max(float(y2 - y1), 1.0)
        cx = float(x1 + w / 2.0)
        cy = float(y1 + h / 2.0)
        area = w * h

        # Update velocity using exponential moving average (EMA)
        if len(self.history_centroids) > 0:
            prev_cx, prev_cy = self.history_centroids[-1]
            prev_frame = self.history_frames[-1]
            dt = max(frame_idx - prev_frame, 1)
            instant_vx = (cx - prev_cx) / dt
            instant_vy = (cy - prev_cy) / dt
            instant_vel = np.array([instant_vx, instant_vy], dtype=np.float32)

            alpha = 0.70  # EMA smoothing factor
            if np.all(self.velocity == 0):
                self.velocity = instant_vel
            else:
                new_velocity = alpha * instant_vel + (1.0 - alpha) * self.velocity
                self.acceleration = (new_velocity - self.velocity) / dt
                self.velocity = new_velocity

        # Append to histories
        self.history_centroids.append((cx, cy))
        self.history_boxes.append((x1, y1, x2, y2))
        self.history_areas.append(area)
        self.history_frames.append(frame_idx)

        # Update state
        self.state = ObjectVisibilityState.VISIBLE
        self.last_seen_frame = frame_idx
        self.frames_visible += 1
        self.frames_occluded = 0
        self.confidence_decay = float(confidence)
        self.predicted_centroid = (cx, cy)
        self.predicted_box = (x1, y1, x2, y2)

    def predict_dead_reckoning(
        self,
        frame_idx: int,
        frame_width: int,
        frame_height: int,
        max_reappearance_gap: int = 90
    ) -> tuple:
        """
        Projects object trajectory forward during sensory absence (dead-reckoning).
        Updates state to OCCLUDED or OUT_OF_BOUNDS.
        """
        self.frames_occluded += 1
        
        # If transitioning from VISIBLE to OCCLUDED, count episode
        if self.state == ObjectVisibilityState.VISIBLE:
            self.total_occlusion_episodes += 1
            self.state = ObjectVisibilityState.OCCLUDED

        # Extrapolate centroid position using current velocity
        last_cx, last_cy = self.history_centroids[-1]
        dt = self.frames_occluded
        
        # Dead-reckoning position: P_pred = P_last + V * dt
        pred_cx = last_cx + float(self.velocity[0]) * dt
        pred_cy = last_cy + float(self.velocity[1]) * dt
        self.predicted_centroid = (pred_cx, pred_cy)

        # Extrapolate bounding box keeping last known dimensions
        last_box = self.history_boxes[-1]
        w = last_box[2] - last_box[0]
        h = last_box[3] - last_box[1]
        
        pred_x1 = pred_cx - w / 2.0
        pred_y1 = pred_cy - h / 2.0
        pred_x2 = pred_cx + w / 2.0
        pred_y2 = pred_cy + h / 2.0
        self.predicted_box = (pred_x1, pred_y1, pred_x2, pred_y2)

        # Decay confidence
        decay_factor = max(0.0, 1.0 - (self.frames_occluded / float(max_reappearance_gap)))
        self.confidence_decay = round(decay_factor, 3)

        # Boundary condition check
        margin = 20  # pixel margin
        is_outside = (
            pred_cx < -margin or pred_cx > (frame_width + margin) or
            pred_cy < -margin or pred_cy > (frame_height + margin)
        )

        if is_outside:
            self.state = ObjectVisibilityState.OUT_OF_BOUNDS
        elif self.frames_occluded > max_reappearance_gap:
            self.state = ObjectVisibilityState.LOST
        else:
            self.state = ObjectVisibilityState.OCCLUDED

        return self.predicted_box, self.state


class PersistentMemoryBank:
    """
    50% Milestone Core Engine: Maintains an explicit memory bank of all tracked entities,
    manages visibility state transitions, performs dead-reckoning extrapolation during occlusion,
    and executes memory-guided re-identification to preserve identity continuity.
    """

    def __init__(
        self,
        frame_width: int = 1920,
        frame_height: int = 1080,
        max_reappearance_gap: int = 90,
        spatial_proximity_thresh: float = 0.35,
        size_similarity_thresh: float = 0.60
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.max_reappearance_gap = max_reappearance_gap
        self.spatial_proximity_thresh = spatial_proximity_thresh
        self.size_similarity_thresh = size_similarity_thresh
        self.diagonal = math.sqrt(frame_width**2 + frame_height**2) if (frame_width and frame_height) else 1.0
        
        # Memory state storage
        self.slots: dict[int, MemoryTrackSlot] = {}
        self.next_master_id = 1
        
        # ID re-mapping table (temporary tracker IDs -> persistent master IDs)
        self.tracker_id_to_master_id: dict[int, int] = {}
        
        # Lifecycle and event audit history
        self.lifecycle_log = []
        self.recovery_events = []

    def update(self, frame_idx: int, detections: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Processes one video frame:
        1. Associates detections with existing memory slots or performs memory re-ID.
        2. Extrapolates missing slots using dead-reckoning.
        3. Returns (enhanced_active_detections, ghost_predictions_for_occluded_objects).
        """
        active_master_ids_this_frame = set()
        enhanced_detections = []
        
        # 1. Group detections by whether they have a known mapped master ID
        unmatched_detections = []
        
        for det in detections:
            raw_track_id = det.get("track_id", -1)
            box = (det["x1"], det["y1"], det["x2"], det["y2"])
            conf = det.get("confidence", 0.0)
            class_name = det.get("class_name", "object")

            if raw_track_id in self.tracker_id_to_master_id:
                master_id = self.tracker_id_to_master_id[raw_track_id]
                slot = self.slots.get(master_id)
                if slot and slot.state == ObjectVisibilityState.VISIBLE:
                    # Continuous tracking confirmation
                    slot.update_visible(frame_idx, box, conf, class_name)
                    active_master_ids_this_frame.add(master_id)
                    
                    det_copy = dict(det)
                    det_copy["raw_track_id"] = raw_track_id
                    det_copy["track_id"] = master_id
                    det_copy["memory_state"] = slot.state.value
                    det_copy["velocity_x"] = round(float(slot.velocity[0]), 2)
                    det_copy["velocity_y"] = round(float(slot.velocity[1]), 2)
                    enhanced_detections.append(det_copy)
                    continue

            unmatched_detections.append(det)

        # 2. Memory-Guided Re-Identification for unmatched/new detections
        # Match against active OCCLUDED slots
        candidate_slots = [
            slot for slot in self.slots.values()
            if slot.state == ObjectVisibilityState.OCCLUDED and slot.track_id not in active_master_ids_this_frame
        ]

        for det in unmatched_detections:
            raw_track_id = det.get("track_id", -1)
            box = (det["x1"], det["y1"], det["x2"], det["y2"])
            w = det["width"]
            h = det["height"]
            det_cx = det["center_x"]
            det_cy = det["center_y"]
            det_area = w * h
            conf = det.get("confidence", 0.0)
            class_name = det.get("class_name", "object")

            best_slot = None
            best_cost = float("inf")
            best_spatial_err = 0.0

            for slot in candidate_slots:
                if slot.track_id in active_master_ids_this_frame:
                    continue
                if slot.class_name.lower() != class_name.lower():
                    continue

                # Predicted coordinates vs detected coordinates
                pred_cx, pred_cy = slot.predicted_centroid if slot.predicted_centroid else slot.history_centroids[-1]
                spatial_dist = math.sqrt((det_cx - pred_cx)**2 + (det_cy - pred_cy)**2)
                norm_dist = spatial_dist / self.diagonal

                # Scale area comparison
                last_area = max(slot.history_areas[-1], 1.0)
                area_ratio = det_area / last_area
                size_diff = abs(area_ratio - 1.0)

                # Cost function: 70% normalized spatial proximity + 30% scale deviation
                cost = (0.70 * norm_dist) + (0.30 * size_diff)

                if norm_dist <= self.spatial_proximity_thresh and size_diff <= self.size_similarity_thresh:
                    if cost < best_cost:
                        best_cost = cost
                        best_slot = slot
                        best_spatial_err = spatial_dist

            if best_slot is not None:
                # SUCCESSFUL MEMORY RECOVERY
                master_id = best_slot.track_id
                self.tracker_id_to_master_id[raw_track_id] = master_id
                
                # Log recovery event
                recovery_record = {
                    "frame": frame_idx,
                    "master_track_id": master_id,
                    "raw_tracker_id": raw_track_id,
                    "class_name": class_name,
                    "occlusion_gap_frames": best_slot.frames_occluded,
                    "prediction_error_px": round(best_spatial_err, 2),
                    "matching_cost": round(best_cost, 4),
                    "event": "MEMORY_RECOVERY_SUCCESS"
                }
                self.recovery_events.append(recovery_record)
                
                # Restore slot to VISIBLE
                best_slot.update_visible(frame_idx, box, conf, class_name)
                active_master_ids_this_frame.add(master_id)
                
                det_copy = dict(det)
                det_copy["raw_track_id"] = raw_track_id
                det_copy["track_id"] = master_id
                det_copy["memory_state"] = best_slot.state.value
                det_copy["velocity_x"] = round(float(best_slot.velocity[0]), 2)
                det_copy["velocity_y"] = round(float(best_slot.velocity[1]), 2)
                enhanced_detections.append(det_copy)
            else:
                # Brand new entity
                if raw_track_id != -1 and raw_track_id not in self.tracker_id_to_master_id:
                    master_id = raw_track_id
                else:
                    master_id = self.next_master_id
                    self.next_master_id += 1

                self.tracker_id_to_master_id[raw_track_id] = master_id
                new_slot = MemoryTrackSlot(
                    track_id=master_id,
                    class_name=class_name,
                    initial_box=box,
                    confidence=conf,
                    frame_idx=frame_idx
                )
                self.slots[master_id] = new_slot
                active_master_ids_this_frame.add(master_id)

                det_copy = dict(det)
                det_copy["raw_track_id"] = raw_track_id
                det_copy["track_id"] = master_id
                det_copy["memory_state"] = new_slot.state.value
                det_copy["velocity_x"] = 0.0
                det_copy["velocity_y"] = 0.0
                enhanced_detections.append(det_copy)

        # 3. Predict dead-reckoning for slots NOT detected in this frame
        ghost_predictions = []
        for master_id, slot in self.slots.items():
            if master_id not in active_master_ids_this_frame:
                pred_box, state = slot.predict_dead_reckoning(
                    frame_idx=frame_idx,
                    frame_width=self.frame_width,
                    frame_height=self.frame_height,
                    max_reappearance_gap=self.max_reappearance_gap
                )
                
                # If currently occluded inside camera bounds, create a Ghost Prediction Box
                if state == ObjectVisibilityState.OCCLUDED:
                    ghost_record = {
                        "track_id": master_id,
                        "class_name": slot.class_name,
                        "state": state.value,
                        "x1": round(pred_box[0], 2),
                        "y1": round(pred_box[1], 2),
                        "x2": round(pred_box[2], 2),
                        "y2": round(pred_box[3], 2),
                        "center_x": round(slot.predicted_centroid[0], 2),
                        "center_y": round(slot.predicted_centroid[1], 2),
                        "frames_occluded": slot.frames_occluded,
                        "confidence_decay": slot.confidence_decay,
                        "velocity_x": round(float(slot.velocity[0]), 2),
                        "velocity_y": round(float(slot.velocity[1]), 2)
                    }
                    ghost_predictions.append(ghost_record)

            # Log frame state into lifecycle log
            self.lifecycle_log.append({
                "frame": frame_idx,
                "master_track_id": master_id,
                "class_name": slot.class_name,
                "state": slot.state.value,
                "frames_visible": slot.frames_visible,
                "frames_occluded": slot.frames_occluded,
                "confidence_decay": slot.confidence_decay,
                "centroid_x": round(slot.predicted_centroid[0], 2) if slot.predicted_centroid else None,
                "centroid_y": round(slot.predicted_centroid[1], 2) if slot.predicted_centroid else None,
                "velocity_x": round(float(slot.velocity[0]), 2),
                "velocity_y": round(float(slot.velocity[1]), 2)
            })

        return enhanced_detections, ghost_predictions

    def get_lifecycle_dataframe(self) -> pd.DataFrame:
        if not self.lifecycle_log:
            return pd.DataFrame(columns=[
                "frame", "master_track_id", "class_name", "state",
                "frames_visible", "frames_occluded", "confidence_decay",
                "centroid_x", "centroid_y", "velocity_x", "velocity_y"
            ])
        return pd.DataFrame(self.lifecycle_log)

    def get_recoveries_dataframe(self) -> pd.DataFrame:
        if not self.recovery_events:
            return pd.DataFrame(columns=[
                "frame", "master_track_id", "raw_tracker_id", "class_name",
                "occlusion_gap_frames", "prediction_error_px", "matching_cost", "event"
            ])
        return pd.DataFrame(self.recovery_events)

    def compute_50_percent_metrics(self) -> dict:
        """Calculates advanced quantitative metrics for the 50% milestone."""
        total_episodes = sum(slot.total_occlusion_episodes for slot in self.slots.values())
        successful_recoveries = len(self.recovery_events)
        
        recovery_rate = (
            round((successful_recoveries / total_episodes) * 100.0, 2)
            if total_episodes > 0 else 100.0
        )
        
        pred_errors = [e["prediction_error_px"] for e in self.recovery_events]
        mean_pred_error = round(float(np.mean(pred_errors)), 2) if pred_errors else 0.0
        max_occlusion_survived = max(
            [e["occlusion_gap_frames"] for e in self.recovery_events],
            default=0
        )

        return {
            "total_occlusion_episodes": total_episodes,
            "successful_memory_recoveries": successful_recoveries,
            "memory_recovery_rate_pct": recovery_rate,
            "mean_trajectory_prediction_error_px": mean_pred_error,
            "max_occlusion_gap_survived_frames": max_occlusion_survived,
            "persistent_entities_count": len(self.slots)
        }
