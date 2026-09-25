import os
import sys
import cv2
import glob
import random
import yaml
import numpy as np

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def prepare_ball_dataset(input_dir="data/input", dataset_dir="data/dataset", sample_interval=5):
    """
    Extracts frames from video files in input_dir and builds a YOLOv8 format dataset.
    Generates dataset.yaml for training.
    """
    print(f"\n==================================================")
    print(f" PREPARING CUSTOM DATASET FOR FINE-TUNING")
    print(f"==================================================")

    images_train_dir = os.path.join(dataset_dir, "images", "train")
    images_val_dir = os.path.join(dataset_dir, "images", "val")
    labels_train_dir = os.path.join(dataset_dir, "labels", "train")
    labels_val_dir = os.path.join(dataset_dir, "labels", "val")

    for d in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
        os.makedirs(d, exist_ok=True)

    video_files = glob.glob(os.path.join(input_dir, "*.mp4")) + \
                  glob.glob(os.path.join(input_dir, "*.avi")) + \
                  glob.glob(os.path.join(input_dir, "*.mov"))

    if not video_files:
        print(f"[ERROR] No video files found in '{input_dir}'.")
        return False

    print(f"[INFO] Found {len(video_files)} video(s) for frame extraction.")

    extracted_samples = []

    for v_path in video_files:
        v_name = os.path.splitext(os.path.basename(v_path))[0]
        cap = cv2.VideoCapture(v_path)
        frame_idx = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            if frame_idx % sample_interval == 0:
                h, w = frame.shape[:2]
                
                # Detect color / circular region for pseudo-label generation
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                # Broader color mask for balls / moving objects
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (9, 9), 2)
                
                # Find motion / circular contours or color contours
                circles = cv2.HoughCircles(
                    blur, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
                    param1=50, param2=30, minRadius=10, maxRadius=int(min(w, h)/4)
                )

                bboxes = []
                if circles is not None:
                    circles = np.uint16(np.around(circles))
                    for i in circles[0, :]:
                        cx, cy, r = i[0], i[1], i[2]
                        x1 = max(0, cx - r - 5)
                        y1 = max(0, cy - r - 5)
                        x2 = min(w, cx + r + 5)
                        y2 = min(h, cy + r + 5)
                        bboxes.append((x1, y1, x2, y2))
                
                # Fallback to visual contours if circles not found
                if not bboxes:
                    edges = cv2.Canny(blur, 50, 150)
                    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in contours:
                        area = cv2.contourArea(cnt)
                        if 300 < area < (w * h * 0.25):
                            x, y, bw, bh = cv2.boundingRect(cnt)
                            aspect_ratio = float(bw) / bh
                            if 0.5 <= aspect_ratio <= 2.0:
                                bboxes.append((x, y, x + bw, y + bh))

                if bboxes:
                    sample_name = f"{v_name}_f{frame_idx:04d}"
                    extracted_samples.append((sample_name, frame, bboxes, w, h))
                    saved_count += 1

        cap.release()
        print(f"[INFO] Extracted {saved_count} candidate frames from {v_name}")

    if not extracted_samples:
        print("[WARNING] No automated candidate regions found. Extracting periodic frames directly.")
        for v_path in video_files:
            v_name = os.path.splitext(os.path.basename(v_path))[0]
            cap = cv2.VideoCapture(v_path)
            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if frame_idx % sample_interval == 0:
                    h, w = frame.shape[:2]
                    sample_name = f"{v_name}_f{frame_idx:04d}"
                    extracted_samples.append((sample_name, frame, [], w, h))
            cap.release()

    # Split train (80%) vs val (20%)
    random.seed(42)
    random.shuffle(extracted_samples)
    split_idx = int(len(extracted_samples) * 0.8)
    train_samples = extracted_samples[:split_idx]
    val_samples = extracted_samples[split_idx:]

    def save_split(samples, img_dir, lbl_dir):
        for sample_name, frame, bboxes, w, h in samples:
            img_path = os.path.join(img_dir, f"{sample_name}.jpg")
            lbl_path = os.path.join(lbl_dir, f"{sample_name}.txt")
            cv2.imwrite(img_path, frame)
            
            with open(lbl_path, "w") as f:
                for x1, y1, x2, y2 in bboxes:
                    # Convert to normalized YOLO format: class x_center y_center width height
                    box_w = (x2 - x1) / w
                    box_h = (y2 - y1) / h
                    x_center = (x1 + (x2 - x1) / 2.0) / w
                    y_center = (y1 + (y2 - y1) / 2.0) / h
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}\n")

    save_split(train_samples, images_train_dir, labels_train_dir)
    save_split(val_samples, images_val_dir, labels_val_dir)

    print(f"[INFO] Dataset preparation complete:")
    print(f"  - Training samples  : {len(train_samples)}")
    print(f"  - Validation samples: {len(val_samples)}")

    # Create dataset.yaml
    abs_dataset_dir = os.path.abspath(dataset_dir).replace("\\", "/")
    dataset_yaml_path = os.path.join(dataset_dir, "dataset.yaml")
    
    dataset_config = {
        "path": abs_dataset_dir,
        "train": "images/train",
        "val": "images/val",
        "names": {
            0: "ball"
        }
    }

    with open(dataset_yaml_path, "w") as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    print(f"[INFO] Generated dataset configuration file: {dataset_yaml_path}")
    print(f"==================================================\n")
    return dataset_yaml_path

if __name__ == "__main__":
    prepare_ball_dataset()
