import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

class PermanenceVisualizer:
    """
    Generates research visualizations for Object Permanence evaluation:
    - Plot 1: Track Lifetimes / Trajectories over time
    - Plot 2: Object Permanence Metrics Bar Chart
    - Plot 3: Disappearance & Identity Switch Event Breakdown
    """

    def __init__(self, output_plots_dir: str):
        self.output_plots_dir = output_plots_dir
        os.makedirs(output_plots_dir, exist_ok=True)
        # Apply clean dark style
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    def plot_track_trajectories(self, detections_df: pd.DataFrame, events_df: pd.DataFrame = None) -> str:
        """Plot 1: Frame Number vs Object Track ID Lifetime Timeline."""
        fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
        
        if detections_df.empty or 'track_id' not in detections_df.columns:
            ax.text(0.5, 0.5, "No tracking data available", ha='center', va='center')
        else:
            valid_df = detections_df[detections_df['track_id'] != -1]
            unique_tracks = sorted(valid_df['track_id'].unique())
            
            colors = plt.cm.tab20(np.linspace(0, 1, max(len(unique_tracks), 1)))
            
            for i, track_id in enumerate(unique_tracks):
                track_data = valid_df[valid_df['track_id'] == track_id].sort_values('frame')
                frames = track_data['frame'].values
                y_vals = np.full_like(frames, track_id)
                
                # Plot continuous line segments
                ax.plot(frames, y_vals, alpha=0.8, linewidth=4, label=f"Track ID {track_id}", color=colors[i % len(colors)])
                ax.scatter(frames, y_vals, s=15, color=colors[i % len(colors)])

            # Annotate events on timeline if available
            if events_df is not None and not events_df.empty:
                for _, event in events_df.iterrows():
                    last_f = event['last_visible_frame']
                    orig_id = event['original_track_id']
                    ev_type = event['event_type']
                    
                    if ev_type in ['IDENTITY_SWITCH', 'TRACK_ID_SWAP']:
                        ax.scatter([last_f], [orig_id], color='red', s=80, zorder=5, marker='X')
                        ax.annotate(f"ID Switch -> {event['new_track_id']}", (last_f, orig_id),
                                    textcoords="offset points", xytext=(0, 10), ha='center',
                                    fontsize=8, color='red', weight='bold')
                    elif ev_type == 'SUCCESSFUL_REIDENTIFICATION':
                        ax.scatter([last_f], [orig_id], color='green', s=70, zorder=5, marker='o')

            ax.set_yticks(unique_tracks)
            ax.set_ylabel("Track ID", fontsize=11, fontweight='bold')
            ax.set_xlabel("Frame Number", fontsize=11, fontweight='bold')
            ax.set_title("Object Track Lifetimes Over Time", fontsize=13, fontweight='bold', pad=12)
            ax.grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        save_path = os.path.join(self.output_plots_dir, "track_trajectories.png")
        fig.savefig(save_path)
        plt.close(fig)
        return save_path

    def plot_metrics_summary(self, metrics_dict: dict) -> str:
        """Plot 2: Object Permanence Score & Consistency Metrics Bar Chart."""
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        
        metrics = metrics_dict.get('metrics', {})
        categories = ['Detection\nConsistency', 'Identity\nConsistency', 'Object Permanence\nScore']
        values = [
            metrics.get('detection_consistency_pct', 0.0),
            metrics.get('identity_consistency_pct', 0.0),
            metrics.get('object_permanence_score_pct', 0.0)
        ]
        
        colors = ['#3498db', '#9b59b6', '#2ecc71']
        bars = ax.bar(categories, values, color=colors, width=0.55, edgecolor='black', linewidth=1.2)
        
        ax.set_ylim(0, 115)
        ax.set_ylabel("Percentage (%)", fontsize=11, fontweight='bold')
        ax.set_title("Object Permanence Evaluation Metrics", fontsize=13, fontweight='bold', pad=12)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        save_path = os.path.join(self.output_plots_dir, "permanence_metrics.png")
        fig.savefig(save_path)
        plt.close(fig)
        return save_path

    def plot_event_breakdown(self, metrics_dict: dict) -> str:
        """Plot 3: Event breakdown chart (Successful Re-IDs vs Switches vs Permanent Losses)."""
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

        events_data = {
            'Successful Re-IDs': metrics_dict.get('successful_reidentifications', 0),
            'Identity Switches': metrics_dict.get('identity_switches', 0),
            'Permanent Losses': metrics_dict.get('lost_without_recovery', 0)
        }

        labels = list(events_data.keys())
        counts = list(events_data.values())
        colors = ['#2ecc71', '#e74c3c', '#e67e22']

        bars = ax.bar(labels, counts, color=colors, width=0.5, edgecolor='black', linewidth=1.2)

        ax.set_ylabel("Event Count", fontsize=11, fontweight='bold')
        ax.set_title("Disappearance & Reappearance Event Breakdown", fontsize=13, fontweight='bold', pad=12)
        ax.set_ylim(0, max(counts) + 3 if max(counts) > 0 else 5)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        save_path = os.path.join(self.output_plots_dir, "event_breakdown.png")
        fig.savefig(save_path)
        plt.close(fig)
        return save_path
