import os
import json
import pandas as pd
import numpy as np

class MetricsCalculator:
    """
    Computes preliminary object permanence research metrics:
    1. Detection Consistency
    2. Identity Consistency
    3. Object Permanence Score
    """

    def __init__(self, video_info: dict):
        self.video_info = video_info

    def compute_metrics(
        self,
        detections_df: pd.DataFrame,
        events_df: pd.DataFrame,
        memory_metrics: dict = None
    ) -> dict:
        total_frames = self.video_info.get("total_frames", 1)
        if total_frames <= 0:
            total_frames = 1

        # 1. Detection Consistency
        if not detections_df.empty and 'frame' in detections_df.columns:
            frames_with_detections = detections_df['frame'].nunique()
            detection_consistency = min(1.0, frames_with_detections / total_frames)
        else:
            frames_with_detections = 0
            detection_consistency = 0.0

        # Unique Tracked Objects count
        if not detections_df.empty and 'track_id' in detections_df.columns:
            valid_tracks = detections_df[detections_df['track_id'] != -1]
            tracked_objects_count = valid_tracks['track_id'].nunique()
        else:
            tracked_objects_count = 0

        # Event counts
        disappearance_events_count = 0
        reappearance_events_count = 0
        successful_reidentifications = 0
        identity_switches = 0
        lost_without_recovery = 0

        if not events_df.empty and 'event_type' in events_df.columns:
            disappearance_events_count = len(events_df)
            successful_reidentifications = len(events_df[events_df['event_type'] == "SUCCESSFUL_REIDENTIFICATION"])
            identity_switches = len(events_df[events_df['event_type'].isin(["IDENTITY_SWITCH", "TRACK_ID_SWAP"])])
            lost_without_recovery = len(events_df[events_df['event_type'] == "DISAPPEARANCE_WITHOUT_RECOVERY"])
            reappearance_events_count = successful_reidentifications + identity_switches

        # 2. Identity Consistency = 1 - (identity switches / total tracked objects)
        if tracked_objects_count > 0:
            identity_consistency = max(0.0, 1.0 - (identity_switches / tracked_objects_count))
        else:
            identity_consistency = 1.0

        # 3. Object Permanence Score = (successful re-identifications) / (total valid disappearance-reappearance events)
        total_reappearance_opportunities = successful_reidentifications + identity_switches
        if total_reappearance_opportunities > 0:
            permanence_score_ratio = successful_reidentifications / total_reappearance_opportunities
        else:
            # If no disappearances/switches occurred, identity remained perfectly intact
            permanence_score_ratio = 1.0

        permanence_score_pct = round(permanence_score_ratio * 100.0, 2)

        summary = {
            "video_file": self.video_info.get("file_name", "N/A"),
            "total_frames": total_frames,
            "duration_sec": self.video_info.get("duration_sec", 0.0),
            "fps": self.video_info.get("fps", 0.0),
            "frames_with_detections": frames_with_detections,
            "tracked_objects_count": tracked_objects_count,
            "disappearance_events_count": disappearance_events_count,
            "reappearance_events_count": reappearance_events_count,
            "successful_reidentifications": successful_reidentifications,
            "identity_switches": identity_switches,
            "lost_without_recovery": lost_without_recovery,
            "metrics": {
                "detection_consistency_pct": round(detection_consistency * 100.0, 2),
                "identity_consistency_pct": round(identity_consistency * 100.0, 2),
                "object_permanence_score_pct": permanence_score_pct
            }
        }

        if memory_metrics:
            summary["memory_bank_metrics"] = memory_metrics

        return summary

    def save_reports(self, summary: dict, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(output_dir, "summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            
        # Save Text Summary Report
        txt_path = os.path.join(output_dir, "summary.txt")
        m = summary['metrics']

        mb_section = ""
        if summary.get("memory_bank_metrics"):
            mb = summary["memory_bank_metrics"]
            mb_section = f"""
--------------------------------------------------
 50% MILESTONE: PERSISTENT MEMORY BANK METRICS
--------------------------------------------------
Persistent Entities Managed:   {mb.get('persistent_entities_count', 0)}
Total Occlusion Episodes:      {mb.get('total_occlusion_episodes', 0)}
Successful Memory Recoveries:  {mb.get('successful_memory_recoveries', 0)}
MEMORY RECOVERY RATE:          {mb.get('memory_recovery_rate_pct', 0.0):.2f}%
Mean Dead-Reckoning Error:     {mb.get('mean_trajectory_prediction_error_px', 0.0):.2f} px
Max Occlusion Gap Survived:    {mb.get('max_occlusion_gap_survived_frames', 0)} frames
"""

        report_text = f"""==================================================
 OBJECT PERMANENCE ANALYSIS REPORT
==================================================

Video File:                  {summary['video_file']}
Total Frames:                {summary['total_frames']} ({summary['duration_sec']} sec @ {summary['fps']} fps)
Frames with Detections:      {summary['frames_with_detections']}
Unique Tracked Objects:      {summary['tracked_objects_count']}

--------------------------------------------------
 EVENT BREAKDOWN
--------------------------------------------------
Total Disappearance Events:  {summary['disappearance_events_count']}
Reappearance Events:         {summary['reappearance_events_count']}
  - Successful Re-IDs:       {summary['successful_reidentifications']}
  - Identity Switches:       {summary['identity_switches']}
Permanent Losses (No Re-ID): {summary['lost_without_recovery']}

--------------------------------------------------
 PRELIMINARY RESEARCH METRICS
--------------------------------------------------
Detection Consistency:       {m['detection_consistency_pct']:.2f}%
Identity Consistency:        {m['identity_consistency_pct']:.2f}%
OBJECT PERMANENCE SCORE:     {m['object_permanence_score_pct']:.2f}%{mb_section}==================================================
"""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        print(f"[INFO] Summary reports saved to: {output_dir}")
        print(report_text)
        return json_path, txt_path
