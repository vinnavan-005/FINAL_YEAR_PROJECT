import os
import math
import pandas as pd
import numpy as np

class ObjectPermanenceAnalyzer:
    """
    Analyzes track life cycles across video frames to identify:
    - Disappearance / Occlusion events
    - Reappearance events
    - Identity Switches (Tracking continuity failure)
    - Successful Re-identifications
    """

    def __init__(
        self,
        min_missing_frames: int = 3,
        max_reappearance_gap: int = 90,
        spatial_proximity_thresh: float = 0.35,
        size_similarity_thresh: float = 0.60,
        frame_width: int = 1920,
        frame_height: int = 1080
    ):
        self.min_missing_frames = min_missing_frames
        self.max_reappearance_gap = max_reappearance_gap
        self.spatial_proximity_thresh = spatial_proximity_thresh
        self.size_similarity_thresh = size_similarity_thresh
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.diagonal = math.sqrt(frame_width**2 + frame_height**2) if (frame_width and frame_height) else 1.0

    def analyze_permanence(self, detections_df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        """
        Analyzes track history DataFrame and returns (events_df, active_alerts_per_frame).
        """
        if detections_df.empty:
            return pd.DataFrame(), []

        # Exclude unassigned track IDs (-1)
        valid_df = detections_df[detections_df['track_id'] != -1].copy()
        if valid_df.empty:
            return pd.DataFrame(), []

        # Map track lifecycle summaries
        tracks = {}
        for track_id, group in valid_df.groupby('track_id'):
            group_sorted = group.sort_values('frame')
            first_row = group_sorted.iloc[0]
            last_row = group_sorted.iloc[-1]
            
            tracks[track_id] = {
                "track_id": track_id,
                "class_name": first_row['class_name'],
                "first_frame": int(first_row['frame']),
                "last_frame": int(last_row['frame']),
                "active_frames": set(group_sorted['frame'].tolist()),
                "total_visible_frames": len(group_sorted),
                "first_box": {
                    "center_x": first_row['center_x'],
                    "center_y": first_row['center_y'],
                    "area": first_row['width'] * first_row['height']
                },
                "last_box": {
                    "center_x": last_row['center_x'],
                    "center_y": last_row['center_y'],
                    "area": last_row['width'] * last_row['height']
                }
            }

        events = []
        event_counter = 1

        # Check self-disappearance and reappearance for each track ID (Same ID)
        for track_id, info in tracks.items():
            active_sorted = sorted(list(info['active_frames']))
            for i in range(len(active_sorted) - 1):
                f_curr = active_sorted[i]
                f_next = active_sorted[i + 1]
                gap = f_next - f_curr - 1
                
                if gap >= self.min_missing_frames:
                    # Same Track ID reappeared after missing frames
                    events.append({
                        "event_id": event_counter,
                        "object_class": info['class_name'],
                        "original_track_id": track_id,
                        "last_visible_frame": f_curr,
                        "first_reappeared_frame": f_next,
                        "missing_duration": gap,
                        "new_track_id": track_id,
                        "event_type": "SUCCESSFUL_REIDENTIFICATION",
                        "reidentified": True,
                        "confidence_score": 1.0,
                        "spatial_distance_norm": 0.0
                    })
                    event_counter += 1

        # Check identity switches across DIFFERENT track IDs
        # Old track terminates -> New track starts later in spatial/temporal proximity
        sorted_track_ids = sorted(tracks.keys(), key=lambda t: tracks[t]['first_frame'])
        
        paired_new_tracks = set()

        for old_id in sorted_track_ids:
            old_info = tracks[old_id]
            f_dis = old_info['last_frame']
            
            best_match_id = None
            best_distance = float('inf')

            for new_id in sorted_track_ids:
                if old_id == new_id or new_id in paired_new_tracks:
                    continue
                    
                new_info = tracks[new_id]
                f_reapp = new_info['first_frame']
                
                # Must start after old track ended within gap limit
                gap = f_reapp - f_dis - 1
                if 0 <= gap <= self.max_reappearance_gap:
                    # Check class compatibility
                    if old_info['class_name'].lower() == new_info['class_name'].lower():
                        # Calculate spatial normalized distance
                        dx = new_info['first_box']['center_x'] - old_info['last_box']['center_x']
                        dy = new_info['first_box']['center_y'] - old_info['last_box']['center_y']
                        dist_px = math.sqrt(dx**2 + dy**2)
                        dist_norm = dist_px / self.diagonal
                        
                        # Area ratio check
                        area_old = max(old_info['last_box']['area'], 1.0)
                        area_new = max(new_info['first_box']['area'], 1.0)
                        area_ratio = area_new / area_old
                        
                        size_valid = (1.0 - self.size_similarity_thresh) <= area_ratio <= (1.0 + self.size_similarity_thresh)
                        
                        if dist_norm <= self.spatial_proximity_thresh and size_valid:
                            if dist_norm < best_distance:
                                best_distance = dist_norm
                                best_match_id = new_id

            if best_match_id is not None:
                new_info = tracks[best_match_id]
                gap = new_info['first_frame'] - f_dis - 1
                
                # Flag Identity Switch event if gap >= min_missing_frames or tracking ID was swapped
                event_type = "IDENTITY_SWITCH" if gap >= self.min_missing_frames else "TRACK_ID_SWAP"
                
                events.append({
                    "event_id": event_counter,
                    "object_class": old_info['class_name'],
                    "original_track_id": old_id,
                    "last_visible_frame": f_dis,
                    "first_reappeared_frame": new_info['first_frame'],
                    "missing_duration": max(gap, 0),
                    "new_track_id": best_match_id,
                    "event_type": event_type,
                    "reidentified": False,
                    "confidence_score": round(1.0 - best_distance, 3),
                    "spatial_distance_norm": round(best_distance, 4)
                })
                event_counter += 1
                paired_new_tracks.add(best_match_id)
            else:
                # Disappearance without recovery check (if track ended significantly before video end)
                max_video_frame = valid_df['frame'].max()
                if (max_video_frame - f_dis) >= self.min_missing_frames and old_id not in [e['original_track_id'] for e in events]:
                    events.append({
                        "event_id": event_counter,
                        "object_class": old_info['class_name'],
                        "original_track_id": old_id,
                        "last_visible_frame": f_dis,
                        "first_reappeared_frame": None,
                        "missing_duration": max_video_frame - f_dis,
                        "new_track_id": None,
                        "event_type": "DISAPPEARANCE_WITHOUT_RECOVERY",
                        "reidentified": False,
                        "confidence_score": 0.0,
                        "spatial_distance_norm": None
                    })
                    event_counter += 1

        events_df = pd.DataFrame(events) if events else pd.DataFrame(columns=[
            "event_id", "object_class", "original_track_id", "last_visible_frame",
            "first_reappeared_frame", "missing_duration", "new_track_id",
            "event_type", "reidentified", "confidence_score", "spatial_distance_norm"
        ])
        
        return events_df, events

    def save_events_to_csv(self, events_df: pd.DataFrame, output_csv_path: str):
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        events_df.to_csv(output_csv_path, index=False)
        print(f"[INFO] Permanence events saved to: {output_csv_path} ({len(events_df)} events)")
        return output_csv_path
