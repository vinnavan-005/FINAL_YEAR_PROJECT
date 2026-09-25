import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.main import process_single_video, load_config

def run():
    video_path = os.path.join("data", "input", "demo_occlusion.mp4")
    output_dir = "outputs"
    config_path = os.path.join("config", "config.yaml")
    
    config = load_config(config_path)
    print("[RUNNER] Starting Object Permanence Evaluation Pipeline...")
    success = process_single_video(video_path, output_dir, config)
    if success:
        print("[RUNNER] Pipeline executed successfully!")
    else:
        print("[RUNNER] Pipeline execution encountered issues.")

if __name__ == "__main__":
    run()
