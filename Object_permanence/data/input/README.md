# Data Input Directory

Place candidate evaluation videos in this directory.

## Supported Video Formats
- `.mp4` (Recommended: H.264 / AVC)
- `.avi`
- `.mov`

## Test Scenarios for Object Permanence Evaluation
For effective academic demonstration, input videos should contain one or more of the following scenarios:

1. **Scenario 1 — Occlusion:**
   - An object moves behind a wall, pillar, tree, or another object, then reappears.
2. **Scenario 2 — Frame Border Disappearance:**
   - An object exits the visible camera frame and re-enters later.
3. **Scenario 3 — Multiple Similar Objects:**
   - Two or more objects of the same class (e.g., two cars or two people) cross paths to test identity retention.
4. **Scenario 4 — AI-Generated Video Failures:**
   - AI generated video clips (e.g., from Sora, Runway Gen-2, Pika, Stable Video Diffusion) where objects morph, vanish, or reappear with changed identity.

## Sample Execution Command
```bash
python src/main.py --input data/input/test_video.mp4
```

To generate a synthetic test video out-of-the-box:
```bash
python tools/create_demo_video.py
```
