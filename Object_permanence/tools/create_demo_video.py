import os
import cv2
import numpy as np

def create_synthetic_occlusion_video(
    output_path: str = "data/input/demo_occlusion.mp4",
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    duration_sec: int = 6
):
    """
    Creates a synthetic test video featuring:
    1. A moving object (simulated car/person) traveling left to right.
    2. A stationary obstacle wall in the middle causing complete occlusion.
    3. Reappearance of the object after exiting occlusion.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = fps * duration_sec
    
    # Object parameters (Simulated red car)
    obj_w, obj_h = 100, 60
    start_x, end_x = 50, width - 150
    obj_y = height // 2 - 30

    # Obstacle Wall parameters (Center pillar)
    wall_x1, wall_x2 = width // 2 - 120, width // 2 + 120
    wall_y1, wall_y2 = 100, height - 100

    print(f"[INFO] Generating synthetic occlusion demo video: {output_path} ({total_frames} frames)...")

    for f in range(1, total_frames + 1):
        # Background: Light grey workspace
        frame = np.full((height, width, 3), (235, 235, 235), dtype=np.uint8)

        # Draw grid lines for visual texture
        for x in range(0, width, 80):
            cv2.line(frame, (x, 0), (x, height), (220, 220, 220), 1)
        for y in range(0, height, 80):
            cv2.line(frame, (0, y), (width, y), (220, 220, 220), 1)

        # Calculate current object position
        progress = (f - 1) / (total_frames - 1)
        obj_x = int(start_x + progress * (end_x - start_x))

        # 1. Draw moving object BEFORE drawing wall overlay
        # Main body (Red box)
        cv2.rectangle(frame, (obj_x, obj_y), (obj_x + obj_w, obj_y + obj_h), (50, 50, 220), -1)
        cv2.rectangle(frame, (obj_x, obj_y), (obj_x + obj_w, obj_y + obj_h), (20, 20, 150), 2)
        # Cabin roof
        roof_x1, roof_x2 = obj_x + 20, obj_x + obj_w - 20
        roof_y1, roof_y2 = obj_y - 25, obj_y
        cv2.rectangle(frame, (roof_x1, roof_y1), (roof_x2, roof_y2), (70, 70, 240), -1)
        # Wheels
        cv2.circle(frame, (obj_x + 25, obj_y + obj_h), 12, (30, 30, 30), -1)
        cv2.circle(frame, (obj_x + obj_w - 25, obj_y + obj_h), 12, (30, 30, 30), -1)
        
        # 2. Draw Obstacle Wall OVER the object (causing true visual occlusion in center frames)
        cv2.rectangle(frame, (wall_x1, wall_y1), (wall_x2, wall_y2), (80, 60, 40), -1)
        cv2.rectangle(frame, (wall_x1, wall_y1), (wall_x2, wall_y2), (40, 30, 20), 3)
        cv2.putText(frame, "OBSTACLE WALL (OCCLUSION)", (wall_x1 + 10, wall_y1 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)

        # Add Frame counter text
        cv2.putText(frame, f"Synthetic Test Video - Frame {f}/{total_frames}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2, cv2.LINE_AA)

        out.write(frame)

    out.release()
    print(f"[INFO] Synthetic test video successfully created at: {output_path}")
    return output_path

if __name__ == "__main__":
    create_synthetic_occlusion_video()
