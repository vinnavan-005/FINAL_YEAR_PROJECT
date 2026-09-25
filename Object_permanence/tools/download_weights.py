import os
import urllib.request

def download_yolo_weights():
    weights_path = "yolov8n.pt"
    url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    
    if not os.path.exists(weights_path):
        print(f"[INFO] Downloading YOLOv8n weights from {url}...")
        urllib.request.urlretrieve(url, weights_path)
        print(f"[INFO] Successfully downloaded {weights_path} ({os.path.getsize(weights_path)} bytes)")
    else:
        print(f"[INFO] Weights file '{weights_path}' already exists.")

if __name__ == "__main__":
    download_yolo_weights()
