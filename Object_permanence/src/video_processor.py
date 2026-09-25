import os
import cv2
import numpy as np

class VideoProcessor:
    """
    Handles video reading, metadata extraction, frame streaming,
    and rendering annotated overlays for detection, tracking, and object permanence events.
    """

    def __init__(self, video_path: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Input video file not found: {video_path}")
        
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"OpenCV failed to open video file: {video_path}")
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0 or np.isnan(self.fps):
            self.fps = 30.0  # Fallback FPS if unreadable
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.writer = None

    def get_info(self) -> dict:
        return {
            "file_name": os.path.basename(self.video_path),
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 2),
            "total_frames": self.total_frames,
            "duration_sec": round(self.total_frames / self.fps, 2) if self.fps > 0 else 0
        }

    def read_frames(self):
        """Generator yielding (frame_index, frame_bgr) starting from frame 1."""
        frame_idx = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame_idx += 1
            yield frame_idx, frame

    def setup_writer(self, output_path: str):
        """Sets up cv2.VideoWriter for annotated output."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        return self.writer

    def write_frame(self, frame):
        if self.writer is not None:
            self.writer.write(frame)

    @staticmethod
    def _generate_color(track_id: int):
        """Generates consistent RGB color palette based on Track ID."""
        np.random.seed(int(track_id) * 37 % 1000)
        color = np.random.randint(50, 230, size=3).tolist()
        return (int(color[0]), int(color[1]), int(color[2]))

    @staticmethod
    def _draw_dashed_rect(img: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int = 2, dash_len: int = 8):
        """Draws a dashed rectangle to represent an occluded/predicted bounding box."""
        x1, y1 = int(min(pt1[0], pt2[0])), int(min(pt1[1], pt2[1]))
        x2, y2 = int(max(pt1[0], pt2[0])), int(max(pt1[1], pt2[1]))
        
        # Horizontal lines
        for x in range(x1, x2, dash_len * 2):
            cv2.line(img, (x, y1), (min(x + dash_len, x2), y1), color, thickness)
            cv2.line(img, (x, y2), (min(x + dash_len, x2), y2), color, thickness)
        # Vertical lines
        for y in range(y1, y2, dash_len * 2):
            cv2.line(img, (x1, y), (x1, min(y + dash_len, y2)), color, thickness)
            cv2.line(img, (x2, y), (x2, min(y + dash_len, y2)), color, thickness)

    def draw_annotations(
        self,
        frame: np.ndarray,
        frame_idx: int,
        detections: list,
        active_alerts: list = None,
        ghost_predictions: list = None
    ) -> np.ndarray:
        """
        Draws bounding boxes, track IDs, labels, top info bar, active alerts,
        and ghost bounding boxes for occluded/predicted objects onto frame.
        """
        annotated = frame.copy()

        # Top Information Bar (Semi-transparent overlay)
        top_bar_height = 45
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, top_bar_height), (20, 24, 33), -1)
        cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)
        
        num_ghosts = len(ghost_predictions) if ghost_predictions else 0
        info_text = f"Frame: {frame_idx}/{self.total_frames} | Active: {len(detections)} | Memory Occluded: {num_ghosts}"
        cv2.putText(annotated, info_text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (240, 240, 240), 2, cv2.LINE_AA)
        
        # Header title
        header_title = "OBJECT PERMANENCE FRAMEWORK (50% MEMORY BANK)"
        (tw, _), _ = cv2.getTextSize(header_title, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cv2.putText(annotated, header_title, (self.width - tw - 15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 215, 255), 1, cv2.LINE_AA)

        # 1. Draw Ghost Predictions for Occluded Entities (Memory Bank Dead-Reckoning)
        if ghost_predictions:
            for ghost in ghost_predictions:
                gx1, gy1 = int(ghost['x1']), int(ghost['y1'])
                gx2, gy2 = int(ghost['x2']), int(ghost['y2'])
                gt_id = ghost['track_id']
                g_cls = ghost['class_name']
                g_gap = ghost['frames_occluded']
                
                ghost_color = (255, 191, 0)  # Cyan/Deep Sky Blue in BGR
                
                # Clip coordinates to frame
                gx1_c = max(0, min(gx1, self.width - 1))
                gy1_c = max(0, min(gy1, self.height - 1))
                gx2_c = max(0, min(gx2, self.width - 1))
                gy2_c = max(0, min(gy2, self.height - 1))

                if gx2_c > gx1_c and gy2_c > gy1_c:
                    # Draw translucent inner fill
                    ghost_overlay = annotated.copy()
                    cv2.rectangle(ghost_overlay, (gx1_c, gy1_c), (gx2_c, gy2_c), ghost_color, -1)
                    cv2.addWeighted(ghost_overlay, 0.15, annotated, 0.85, 0, annotated)

                    # Draw dashed outline
                    self._draw_dashed_rect(annotated, (gx1_c, gy1_c), (gx2_c, gy2_c), ghost_color, thickness=2, dash_len=6)

                    # Draw center prediction crosshair
                    pcx, pcy = int(ghost['center_x']), int(ghost['center_y'])
                    if 0 <= pcx < self.width and 0 <= pcy < self.height:
                        cv2.drawMarker(annotated, (pcx, pcy), ghost_color, cv2.MARKER_CROSS, 12, 1)

                    # Badge: "[OCCLUDED] Ball | ID 1 (t-5)"
                    ghost_label = f"[OCCLUDED] {g_cls.capitalize()} | ID {gt_id} (t-{g_gap})"
                    (gl_w, gl_h), _ = cv2.getTextSize(ghost_label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                    gl_y1 = max(gy1_c - gl_h - 8, 0)
                    gl_y2 = gl_y1 + gl_h + 6
                    gl_x2 = min(gx1_c + gl_w + 8, self.width)
                    
                    cv2.rectangle(annotated, (gx1_c, gl_y1), (gl_x2, gl_y2), (40, 40, 40), -1)
                    cv2.rectangle(annotated, (gx1_c, gl_y1), (gl_x2, gl_y2), ghost_color, 1)
                    cv2.putText(annotated, ghost_label, (gx1_c + 4, gl_y2 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, ghost_color, 1, cv2.LINE_AA)

        # 2. Draw Active Detections
        for det in detections:
            track_id = det.get('track_id', 'N/A')
            class_name = det.get('class_name', 'object')
            conf = det.get('confidence', 0.0)
            mem_state = det.get('memory_state', 'VISIBLE')
            x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
            
            color = self._generate_color(track_id if isinstance(track_id, int) else 0)
            
            # Draw Bounding Box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Corner accents
            line_len = min(15, int((x2 - x1) / 4), int((y2 - y1) / 4))
            if line_len > 0:
                cv2.line(annotated, (x1, y1), (x1 + line_len, y1), color, 4)
                cv2.line(annotated, (x1, y1), (x1, y1 + line_len), color, 4)
                cv2.line(annotated, (x2, y2), (x2 - line_len, y2), color, 4)
                cv2.line(annotated, (x2, y2), (x2, y2 - line_len), color, 4)

            # Label box: "Class | ID X [VISIBLE] (0.91)"
            label = f"{class_name.capitalize()} | ID {track_id}"
            if mem_state == "VISIBLE":
                label += " [VISIBLE]"
            if conf > 0:
                label += f" | {conf:.2f}"
                
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            
            # Label background box above or inside
            lbl_y1 = max(y1 - label_h - 10, 0)
            lbl_y2 = lbl_y1 + label_h + 8
            lbl_x2 = min(x1 + label_w + 12, self.width)
            
            cv2.rectangle(annotated, (x1, lbl_y1), (lbl_x2, lbl_y2), color, -1)
            cv2.putText(annotated, label, (x1 + 6, lbl_y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        # 3. Draw Active Alerts / Event notifications on bottom right/left
        if active_alerts:
            alert_y = top_bar_height + 25
            for alert in active_alerts:
                (aw, ah), _ = cv2.getTextSize(alert['text'], cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                bg_color = alert.get('color', (0, 0, 220)) # default red
                
                alert_overlay = annotated.copy()
                cv2.rectangle(alert_overlay, (15, alert_y - 20), (25 + aw, alert_y + 8), bg_color, -1)
                cv2.addWeighted(alert_overlay, 0.8, annotated, 0.2, 0, annotated)
                
                cv2.putText(annotated, alert['text'], (20, alert_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
                alert_y += 35

        return annotated

    def close(self):
        if self.cap is not None:
            self.cap.release()
        if self.writer is not None:
            self.writer.release()
