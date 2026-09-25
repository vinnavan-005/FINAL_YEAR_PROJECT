# Object Permanence in AI-Generated Videos
> **Final-Year Undergraduate Research Project — 30% Working Prototype & Evaluation Framework**

---

## 1. Project Overview

AI-generated videos (produced by modern diffusion models, video transformers, and generative world models) often display high visual photorealism. However, they frequently exhibit **temporal consistency failures** and lack fundamental physical constraints—most notably **Object Permanence** (the cognitive understanding that objects continue to exist even when hidden from view).

This repository implements the **30% initial working prototype** of the research project: an automated **Object Permanence Evaluation Framework**. It uses pretrained computer vision models (**YOLOv8** object detection and **ByteTrack** multi-object tracking) to track object identities, detect occlusion and disappearance events, flag identity switches, and calculate quantitative object permanence metrics.

---

## 2. Research Problem

When an object in an AI-generated video undergoes occlusion (e.g. passing behind another object, exiting the camera frame, or turning away), video generation models often fail to preserve object identity:
- An object **changes identity** (reappears with a new track ID or altered appearance).
- An object **vanishes permanently** when it should logically reappear.
- Multiple similar objects cause **identity swapping**.
- Visual characteristics or category classifications morph dynamically.

### Core Research Question (30% Stage)
> **Can object detection and multi-object tracking be systematically leveraged to measure and quantify object permanence failures in AI-generated videos?**

---

## 3. System Architecture & Pipeline

```text
                    INPUT VIDEO (.mp4 / .avi / .mov)
                         |
                         v
               +-------------------+
               |   OpenCV Video    |
               |     Processing    |
               +---------+---------+
                         |
                         v
               +-------------------+
               |   YOLO Object     |
               |  Detection (v8n)  |
               +---------+---------+
                         |
                         v
               +-------------------+
               |  ByteTrack Object |
               |     Tracking      |
               +---------+---------+
                         |
                         v
               +-------------------+
               | Disappearance /   |
               | Occlusion Analysis|
               +---------+---------+
                         |
                         v
               +-------------------+
               | Re-identification |
               |  & Identity Switch|
               +---------+---------+
                         |
                         v
               +-------------------+
               | Object Permanence |
               |     Metrics       |
               +---------+---------+
                         |
                         v
               +-------------------+
               | Visualization +   |
               | CSV/JSON Reports  |
               +-------------------+
```

---

## 4. Repository Structure

```text
Object permanence/
│
├── README.md                          # Academic project documentation & demonstration guide
├── requirements.txt                   # Dependency list
├── .gitignore                         # Output and weight file exclusions
│
├── config/
│   └── config.yaml                    # System configuration & analysis thresholds
│
├── data/
│   ├── input/
│   │   └── README.md                  # Test video guidelines & format support
│   ├── output/
│   └── results/
│
├── outputs/                           # Generated evaluation outputs
│   ├── annotated_videos/              # Rendered video with track IDs and alert overlays
│   ├── plots/                         # Trajectory timelines and evaluation charts
│   └── reports/                       # CSV detection history, permanence events, JSON/TXT summaries
│
├── src/
│   ├── __init__.py
│   ├── video_processor.py             # Video I/O, FPS/metadata parsing, overlay renderer
│   ├── detector_tracker.py            # YOLO + ByteTrack wrapper & frame logger
│   ├── permanence_analyzer.py         # Track lifecycle analysis & event classification
│   ├── metrics.py                     # Detection Consistency, Identity Consistency, Permanence Score
│   ├── visualization.py               # Trajectory timeline & metric bar charts
│   └── main.py                        # CLI entry point
│
├── tools/
│   └── create_demo_video.py           # Synthetic occlusion test video generator
│
└── notebooks/
    └── analysis.ipynb                 # Interactive Jupyter demonstration notebook
```

---

## 5. Installation & Environment Setup

This project uses the Python virtual environment located at `c:\Users\ersib\Desktop\NVIDIA\venv`.

### Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
..\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
..\venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source ../venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 6. Execution & Usage Guide

### Option A: Out-of-the-Box Demo Run (Synthetic Video)

1. **Generate synthetic occlusion test video:**
   ```bash
   python tools/create_demo_video.py
   ```
   *(Creates `data/input/demo_occlusion.mp4` featuring an object passing behind a wall obstacle).*

2. **Run evaluation framework:**
   ```bash
   python src/main.py --input data/input/demo_occlusion.mp4
   ```

### Option B: Evaluate Custom Video

```bash
python src/main.py --input data/input/your_video.mp4 --output outputs/
```

### Option C: Focus Analysis on Target Object Category

```bash
python src/main.py --input data/input/traffic.mp4 --target car
```

### Option D: Batch Directory Processing

```bash
python src/main.py --input_dir data/input/
```

---

## 7. Metrics & Definitions

The framework computes three preliminary research metrics:

### 1. Detection Consistency (%)
Measures the proportion of video frames where objects are successfully detected:
$$\text{Detection Consistency} = \frac{\text{Frames with Active Detections}}{\text{Total Video Frames}} \times 100\%$$

### 2. Identity Consistency (%)
Quantifies how effectively tracked objects maintain persistent identities without tracking swaps:
$$\text{Identity Consistency} = \max\left(0, 1 - \frac{\text{Identity Switches}}{\text{Total Tracked Objects}}\right) \times 100\%$$

### 3. Object Permanence Score (%)
Measures the ratio of correctly preserved object identity events following disappearance/occlusion:
$$\text{Object Permanence Score} = \frac{\text{Successful Re-identifications}}{\text{Total Disappearance-Reappearance Events}} \times 100\%$$

---

## 8. Output Deliverables

After running an evaluation, the framework generates:

1. **Annotated Output Video (`outputs/annotated_videos/<name>_annotated.mp4`):**
   - Displays bounding boxes, `Class | ID X` badges, confidence scores, frame counters, and real-time event alert banners.
2. **Detections History CSV (`outputs/reports/<name>_detections.csv`):**
   - Per-frame tracking records: `frame, track_id, class_name, confidence, x1, y1, x2, y2, center_x, center_y, width, height`.
3. **Permanence Events CSV (`outputs/reports/<name>_events.csv`):**
   - Log of disappearance/reappearance events: `event_id, object_class, original_track_id, last_visible_frame, first_reappeared_frame, missing_duration, new_track_id, event_type, reidentified`.
4. **Summary Reports (`outputs/reports/summary.json` and `summary.txt`):**
   - Complete numerical breakdown and metric results.
5. **Visualizations (`outputs/plots/`):**
   - `track_trajectories.png`: Timeline graph of object track lifetimes and identity switches over frame indices.
   - `permanence_metrics.png`: Bar chart of performance metrics.
   - `event_breakdown.png`: Categorical breakdown of tracking outcomes.

---

## 9. Academic Project Review & Viva Presentation Guide

When demonstrating this **30% prototype** in an academic review:

1. **Explain the Scope:**
   - Clearly state that this prototype is an **Evaluation Framework**, not a generative AI model.
   - It provides an automated, objective methodology for scoring object-permanence quality in video generation models.
2. **Demonstrate the Pipeline:**
   - Run the main script on the demo video:
     `python src/main.py --input data/input/demo_occlusion.mp4`
   - Play the resulting annotated video from `outputs/annotated_videos/` to visually show detection, track ID assignment, and occlusion handling.
   - Open `outputs/plots/track_trajectories.png` to explain how track disappearance and identity continuity are analyzed over time.
3. **Review the Metrics Report:**
   - Present `outputs/reports/summary.txt` to display the calculated Object Permanence Score.

---

## 10. Research Limitations (Academic Honesty)

- **Pretrained Tracker Constraints:** Neither YOLO nor ByteTrack possesses cognitive memory or 3D spatial awareness. If ByteTrack fails due to long occlusion, the framework registers an identity switch event, which correctly highlights an object permanence limitation in the video sequence.
- **2D Spatial Proximity Heuristics:** Re-identification matching currently relies on 2D frame coordinate distances and bounding box area ratios rather than deep visual feature embeddings.

---

## 11. Future Research Roadmap (70% Remaining Scope)

- **Stage 2 (Persistent Object State Memory Bank):** Maintain a long-term memory bank storing spatial coordinates, estimated velocities, bounding box sizes, and visibility states (`VISIBLE`, `OCCLUDED`, `OUT_OF_BOUNDS`).
- **Stage 3 (Deep Visual Feature Re-ID):** Integrate a pretrained appearance embedding extractor (e.g., OSNet / Re-ID transformer) to compare visual similarity across long disappearance gaps.
- **Stage 4 (Depth-Aware Spatial Tracking):** Incorporate monocular depth estimation (e.g. Depth Anything) to track object trajectories behind occluders in 3D camera space.
- **Stage 5 (Memory-Conditioned Benchmark Dataset):** Evaluate and benchmark state-of-the-art AI video generation models (Sora, Runway Gen-2, Pika, SVD) across standard occlusion, camera movement, and multi-object test suites.
