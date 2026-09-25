# Final Year Project: Object Permanence Evaluation & Memory Bank Framework for AI-Generated Videos

This repository contains the comprehensive research, dataset analysis framework, model pipeline, and evaluation benchmarks for investigating and resolving **Object Permanence failures in AI-Generated Videos**.

---

## 📌 Project Overview
Generative video models (e.g., Sora, Runway Gen-2, Pika, VideoCrafter) frequently violate basic laws of intuitive physics. Objects that become occluded behind obstacles often morph, lose identity, or vanish permanently upon reappearance.

This project implements:
1. **Zero-Shot Open-Vocabulary Detection & Tracking:** Powered by YOLO-World and ByteTrack.
2. **50% Milestone - Persistent Memory Bank:** An explicit state machine (`VISIBLE`, `OCCLUDED`, `OUT_OF_BOUNDS`, `LOST`) with ballistic dead-reckoning extrapolation and kinematic cost matching to preserve entity identity across severe occlusions.
3. **Automated Quantitative Research Metrics:** Measuring Detection Consistency, Identity Consistency, and Object Permanence Score.
4. **Comprehensive Research Artifacts:** Complete IEEE-style research papers, project abstracts, architecture diagrams, and empirical reports.

---

## 📂 Repository Structure

```
FINAL_YEAR_PROJECT/
├── Object_permanence/                     # Core Project Root
│   ├── config/                            # YAML Pipeline & Memory Bank Configurations
│   │   └── config.yaml
│   ├── data/
│   │   └── input/                         # Test videos with challenging occlusions
│   ├── outputs/
│   │   ├── annotated_videos/              # Rendered MP4s with ghost boxes and status tags
│   │   ├── plots/                         # Trajectory, breakdown, and metric graphs
│   │   └── reports/                       # CSV lifecycle audits, recoveries, and summary reports
│   ├── src/                               # Source Code Modules
│   │   ├── detector_tracker.py            # YOLO-World + ByteTrack integration
│   │   ├── memory_bank.py                 # 50% Persistent Memory Bank Engine
│   │   ├── metrics.py                     # Quantitative permanence metrics calculator
│   │   ├── permanence_analyzer.py         # Temporal occlusion & switch event analyzer
│   │   ├── video_processor.py             # OpenCV rendering (dashed ghost boxes, HUD)
│   │   └── visualization.py               # Research plot visualizers
│   ├── tools/                             # Demo creation & utility scripts
│   ├── Research_Paper_Final.pdf           # Formal IEEE Research Paper
│   ├── architecture_diagram.jpg           # Visual Architecture Diagram
│   ├── main.py                            # Primary execution entrypoint
│   └── README.md                          # Detailed module documentation
├── Abstract.docx                          # Project Abstract Version 1
├── Abstract 2.docx                        # Project Abstract Version 2
├── Object_Permanence_Abstract.docx        # Specialized Research Abstract
├── Research_Paper_Object_Permanence.docx  # Full Research Paper Source Document
├── requirements.txt                       # Python dependencies
└── .gitignore                             # Ignored files (venv, large weights, etc.)
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/vinnavan-005/FINAL_YEAR_PROJECT.git
cd FINAL_YEAR_PROJECT
```

### 2. Set Up the Python Virtual Environment
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Evaluation Pipeline
Execute tracking with the **Persistent Memory Bank** enabled:
```bash
cd Object_permanence
python src/main.py --input data/input/TESTBALL.mp4
```

To run batch processing on all test videos:
```bash
python src/main.py --input_dir data/input
```

---

## 📊 Key Milestone Metrics (50% Completion)
- **Identity Consistency:** 100.00%
- **Object Permanence Score:** 100.00%
- **Memory Recovery Rate:** 71.43% on benchmark occlusion trials
- **Dead-Reckoning Visuals:** Real-time dashed cyan ghost bounding boxes showing projected object trajectories during sensory absence.
