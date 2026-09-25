import os
import sys
import shutil
import yaml

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ultralytics import YOLO

def train_custom_yolo():
    print(f"\n==================================================")
    print(f" CUSTOM YOLOv8 FINE-TUNING ON RTX 4060 GPU")
    print(f"==================================================")

    # 1. Ensure dataset exists
    dataset_yaml = os.path.join("data", "dataset", "dataset.yaml")
    if not os.path.exists(dataset_yaml):
        print(f"[INFO] Dataset YAML not found at '{dataset_yaml}'. Running dataset preparation script...")
        try:
            from tools.prepare_dataset import prepare_ball_dataset
        except ImportError:
            from prepare_dataset import prepare_ball_dataset
        dataset_yaml = prepare_ball_dataset()

    print(f"[INFO] Using dataset configuration: {dataset_yaml}")

    # 2. Load Base YOLOv8 Medium Model
    base_model_weights = "yolov8m.pt"
    print(f"[INFO] Loading base model weights: {base_model_weights}...")
    model = YOLO(base_model_weights)

    # 3. Train Model on NVIDIA RTX 4060 GPU
    output_run_dir = os.path.join("outputs", "train_run")
    os.makedirs(output_run_dir, exist_ok=True)

    print(f"[INFO] Launching 25-epoch fine-tuning on NVIDIA GeForce RTX 4060 GPU (device=0)...")
    
    results = model.train(
        data=dataset_yaml,
        epochs=25,
        imgsz=1280,
        batch=4,
        device=0,
        workers=2,
        project="outputs",
        name="custom_ball_run",
        exist_ok=True,
        verbose=True,
        # Heavy Video Augmentations
        degrees=15.0,
        translate=0.1,
        scale=0.2,
        flipud=0.0,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        erasing=0.2
    )

    # 4. Locate Best Weights and Save to Project Weights Folder
    best_weights_src = os.path.join("outputs", "custom_ball_run", "weights", "best.pt")
    target_weights_dir = "weights"
    os.makedirs(target_weights_dir, exist_ok=True)
    target_weights_path = os.path.join(target_weights_dir, "custom_ball_yolov8m.pt")

    if os.path.exists(best_weights_src):
        shutil.copy(best_weights_src, target_weights_path)
        print(f"[INFO] Custom fine-tuned weights successfully saved to: {target_weights_path}")
    else:
        print(f"[WARNING] Could not locate best weights at '{best_weights_src}'. Check output training logs.")

    # 5. Automatically Update config/config.yaml to Use Custom Model
    config_path = os.path.join("config", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        
        cfg["model"]["yolo_weights"] = target_weights_path.replace("\\", "/")
        
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False)
        print(f"[INFO] Updated {config_path} to use custom weights: {target_weights_path}")

    print(f"==================================================")
    print(f" FINE-TUNING COMPLETE & MODEL DEPLOYED")
    print(f"==================================================\n")

if __name__ == "__main__":
    train_custom_yolo()
