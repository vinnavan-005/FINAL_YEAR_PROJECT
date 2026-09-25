import os
import glob
import pandas as pd

reports_dir = os.path.join("outputs", "reports")
csv_files = sorted(glob.glob(os.path.join(reports_dir, "*_detections.csv")))

print("==================================================")
print(" HIGH-RESOLUTION DETECTION RESULTS ANALYSIS")
print("==================================================")
for f in csv_files:
    fname = os.path.basename(f)
    df = pd.read_csv(f)
    num_records = len(df)
    if num_records > 0:
        classes = df["class_name"].unique().tolist()
        avg_conf = df["confidence"].mean()
        min_conf = df["confidence"].min()
        max_conf = df["confidence"].max()
        unique_frames = df["frame"].nunique()
        print(f"File: {fname:25s} | Records: {num_records:4d} | Frames: {unique_frames:4d} | Classes: {classes} | Avg Conf: {avg_conf:.2f} (Range: {min_conf:.2f}-{max_conf:.2f})")
    else:
        print(f"File: {fname:25s} | Records: 0 (No detections above 0.50 threshold)")
print("==================================================")
