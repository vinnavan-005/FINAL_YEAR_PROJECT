import os
import sys
import argparse
import yaml
import glob
import pandas as pd
from tqdm import tqdm

# Ensure src modules are resolvable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video_processor import VideoProcessor
from src.detector_tracker import ObjectDetectorTracker
from src.permanence_analyzer import ObjectPermanenceAnalyzer
from src.metrics import MetricsCalculator
from src.visualization import PermanenceVisualizer
from src.memory_bank import PersistentMemoryBank

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"[WARNING] Config file '{config_path}' not found. Using default settings.")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def process_single_video(
    video_path: str,
    output_base_dir: str,
    config: dict,
    target_class: str = None,
    prompts: list = None
):
    print(f"\n==================================================")
    print(f" PROCESSING VIDEO: {video_path}")
    print(f"==================================================")

    # Resolve output subdirectories
    video_basename = os.path.splitext(os.path.basename(video_path))[0]
    annotated_video_dir = os.path.join(output_base_dir, "annotated_videos")
    reports_dir = os.path.join(output_base_dir, "reports")
    plots_dir = os.path.join(output_base_dir, "plots")
    
    os.makedirs(annotated_video_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    # 1. Video Processing & Metadata
    try:
        vp = VideoProcessor(video_path)
    except Exception as e:
        print(f"[ERROR] Failed to initialize video processor: {e}")
        return False

    v_info = vp.get_info()
    print(f"[INFO] Resolution: {v_info['width']}x{v_info['height']} | FPS: {v_info['fps']} | Total Frames: {v_info['total_frames']}")

    # 2. Object Detector & Tracker Setup
    model_cfg = config.get("model", {})
    weights = model_cfg.get("yolo_weights", "yolov8x-worldv2.pt")
    tracker_config = model_cfg.get("tracker_config", "bytetrack.yaml")
    conf_thresh = model_cfg.get("conf_threshold", 0.25)
    iou_thresh = model_cfg.get("iou_threshold", 0.45)
    img_size = model_cfg.get("img_size", 1280)
    device = model_cfg.get("device", "cpu")
    custom_prompts = prompts or model_cfg.get("custom_prompts", ["ball", "box"])

    detector_tracker = ObjectDetectorTracker(
        weights=weights,
        tracker_config=tracker_config,
        conf_threshold=conf_thresh,
        iou_threshold=iou_thresh,
        img_size=img_size,
        device=device,
        target_class=target_class,
        custom_prompts=custom_prompts
    )

    # 50% Milestone: Initialize Persistent Memory Bank
    mem_cfg = config.get("memory_bank", {})
    mem_enabled = mem_cfg.get("enabled", True)
    render_ghost_boxes = mem_cfg.get("render_ghost_boxes", True)
    memory_bank = None
    if mem_enabled:
        memory_bank = PersistentMemoryBank(
            frame_width=v_info['width'],
            frame_height=v_info['height'],
            max_reappearance_gap=mem_cfg.get("max_reappearance_gap", 90),
            spatial_proximity_thresh=mem_cfg.get("spatial_proximity_thresh", 0.35),
            size_similarity_thresh=mem_cfg.get("size_similarity_thresh", 0.60)
        )
        print(f"[INFO] 50% Milestone Persistent Memory Bank ACTIVE.")

    output_video_path = os.path.join(annotated_video_dir, f"{video_basename}_annotated.mp4")
    vp.setup_writer(output_video_path)

    print(f"[INFO] Executing YOLO + ByteTrack + Memory Bank on frames...")
    
    # 3. Frame-by-Frame Detection, Memory State Updating & Rendering
    persistent_detections_history = []

    for frame_idx, frame in tqdm(vp.read_frames(), total=v_info['total_frames'], desc="Processing"):
        # Track objects with ByteTrack
        raw_detections = detector_tracker.process_frame(frame, frame_idx)
        
        ghost_predictions = []
        if memory_bank is not None:
            # Memory Bank: track reconciliation, kinematic update, dead-reckoning extrapolation
            frame_detections, ghost_predictions = memory_bank.update(frame_idx, raw_detections)
            persistent_detections_history.extend(frame_detections)
        else:
            frame_detections = raw_detections

        # Render annotated frame with active detections and dead-reckoned ghost boxes
        draw_ghosts = ghost_predictions if render_ghost_boxes else None
        annotated_frame = vp.draw_annotations(frame, frame_idx, frame_detections, ghost_predictions=draw_ghosts)
        vp.write_frame(annotated_frame)

    vp.close()
    
    # 4. Save Detections History CSV
    detections_csv = os.path.join(reports_dir, f"{video_basename}_detections.csv")
    if memory_bank is not None and persistent_detections_history:
        detections_df = pd.DataFrame(persistent_detections_history)
        detections_df.to_csv(detections_csv, index=False)
        print(f"[INFO] Persistent detections history saved to: {detections_csv} ({len(detections_df)} records)")
    else:
        detections_df = detector_tracker.get_dataframe()
        detector_tracker.save_to_csv(detections_csv)

    # 4b. Export Memory Bank Lifecycle & Recoveries CSVs
    memory_metrics = None
    if memory_bank is not None:
        lifecycle_csv = os.path.join(reports_dir, f"{video_basename}_memory_lifecycle.csv")
        recoveries_csv = os.path.join(reports_dir, f"{video_basename}_memory_recoveries.csv")
        
        lifecycle_df = memory_bank.get_lifecycle_dataframe()
        recoveries_df = memory_bank.get_recoveries_dataframe()
        
        lifecycle_df.to_csv(lifecycle_csv, index=False)
        recoveries_df.to_csv(recoveries_csv, index=False)
        print(f"[INFO] Memory Bank lifecycle log saved to: {lifecycle_csv} ({len(lifecycle_df)} records)")
        print(f"[INFO] Memory Bank recoveries log saved to: {recoveries_csv} ({len(recoveries_df)} recoveries)")
        
        memory_metrics = memory_bank.compute_50_percent_metrics()

    # 5. Permanence & Identity Switch Analysis
    analysis_cfg = config.get("analysis", {})
    analyzer = ObjectPermanenceAnalyzer(
        min_missing_frames=analysis_cfg.get("min_missing_frames", 3),
        max_reappearance_gap=analysis_cfg.get("max_reappearance_gap", 90),
        spatial_proximity_thresh=analysis_cfg.get("spatial_proximity_thresh", 0.35),
        size_similarity_thresh=analysis_cfg.get("size_similarity_thresh", 0.60),
        frame_width=v_info['width'],
        frame_height=v_info['height']
    )

    events_df, events_list = analyzer.analyze_permanence(detections_df)
    events_csv = os.path.join(reports_dir, f"{video_basename}_events.csv")
    analyzer.save_events_to_csv(events_df, events_csv)

    # 6. Research Metrics Calculation
    metrics_calc = MetricsCalculator(v_info)
    summary_report = metrics_calc.compute_metrics(detections_df, events_df, memory_metrics=memory_metrics)
    metrics_calc.save_reports(summary_report, reports_dir)

    # 7. Plots Generation
    visualizer = PermanenceVisualizer(plots_dir)
    p1 = visualizer.plot_track_trajectories(detections_df, events_df)
    p2 = visualizer.plot_metrics_summary(summary_report)
    p3 = visualizer.plot_event_breakdown(summary_report)

    # 8. Console Completion Summary
    m = summary_report['metrics']
    print(f"\n========================================")
    print(f" OBJECT PERMANENCE ANALYSIS COMPLETE")
    print(f"========================================")
    print(f"Input Video:              {video_path}")
    print(f"Annotated Video Output:   {output_video_path}")
    print(f"Detection History CSV:    {detections_csv}")
    print(f"Permanence Events CSV:    {events_csv}")
    if memory_metrics:
        print(f"Memory Lifecycle CSV:     {lifecycle_csv}")
        print(f"Memory Recoveries CSV:    {recoveries_csv}")
    print(f"\nMetrics:")
    print(f"  Detection Consistency:  {m['detection_consistency_pct']:.2f}%")
    print(f"  Identity Consistency:   {m['identity_consistency_pct']:.2f}%")
    print(f"  Object Permanence Score: {m['object_permanence_score_pct']:.2f}%")
    if memory_metrics:
        print(f"\n50% Milestone Memory Bank Metrics:")
        print(f"  Occlusion Episodes:     {memory_metrics['total_occlusion_episodes']}")
        print(f"  Memory Recoveries:      {memory_metrics['successful_memory_recoveries']}")
        print(f"  Memory Recovery Rate:   {memory_metrics['memory_recovery_rate_pct']:.2f}%")
        print(f"  Mean Dead-Reckon Error: {memory_metrics['mean_trajectory_prediction_error_px']:.2f} px")
        print(f"  Max Occlusion Survived: {memory_metrics['max_occlusion_gap_survived_frames']} frames")
    print(f"\nReports Directory:       {reports_dir}")
    print(f"Plots Directory:         {plots_dir}")
    print(f"========================================\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="Object Permanence in AI-Generated Videos - 50% Persistent Memory Bank Framework")
    parser.add_argument("--input", type=str, default=None, help="Path to single input video (.mp4, .avi, .mov)")
    parser.add_argument("--input_dir", type=str, default=None, help="Path to directory containing input videos for batch processing")
    parser.add_argument("--output", type=str, default="outputs", help="Output base directory (default: outputs/)")
    parser.add_argument("--target", type=str, default=None, help="Optional target class filter (e.g. 'car', 'person', 'bottle')")
    parser.add_argument("--prompts", type=str, default=None, help="Comma-separated open-vocabulary text prompts for YOLO-World (e.g. 'ball, box')")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to YAML configuration file")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    parsed_prompts = [p.strip() for p in args.prompts.split(",")] if args.prompts else None

    if not args.input and not args.input_dir:
        # Default fallback to demo video if available or instruct user
        default_demo = os.path.join("data", "input", "demo_occlusion.mp4")
        if os.path.exists(default_demo):
            args.input = default_demo
        else:
            print("[ERROR] Please specify an input video via '--input <path>' or input directory via '--input_dir <dir>'.")
            print("Tip: Run 'python tools/create_demo_video.py' to generate a synthetic test video automatically.")
            sys.exit(1)

    if args.input_dir:
        if not os.path.exists(args.input_dir):
            print(f"[ERROR] Specified input directory '{args.input_dir}' does not exist.")
            sys.exit(1)
        video_files = glob.glob(os.path.join(args.input_dir, "*.mp4")) + \
                      glob.glob(os.path.join(args.input_dir, "*.avi")) + \
                      glob.glob(os.path.join(args.input_dir, "*.mov"))
        if not video_files:
            print(f"[ERROR] No video files found in directory '{args.input_dir}'.")
            sys.exit(1)
        print(f"[INFO] Found {len(video_files)} video(s) in '{args.input_dir}' for batch processing.")
        for v_path in video_files:
            process_single_video(v_path, args.output, config, target_class=args.target, prompts=parsed_prompts)
    else:
        if not os.path.exists(args.input):
            print(f"[ERROR] Input video '{args.input}' not found.")
            sys.exit(1)
        process_single_video(args.input, args.output, config, target_class=args.target, prompts=parsed_prompts)

if __name__ == "__main__":
    main()
