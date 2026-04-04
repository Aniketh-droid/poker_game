import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def plot_match_stats(chip_deltas: list[float], entropy_history: list[float], name: str, agent1_name: str, agent2_name: str, save_path: str = None, wins1: float = 0, wins2: float = 0, ties: float = 0):
    """
    Plots cumulative chip delta, entropy history, and a win/loss pie chart for a match.
    """
    if not chip_deltas:
        print("No chip deltas to plot.")
        return

    # Compute cumulative chips
    cumulative_chips = [sum(chip_deltas[:i+1]) for i in range(len(chip_deltas))]
    
    # Create 3 subplots: Profit (top left), Entropy (bottom left), Pie Chart (right)
    fig = plt.figure(figsize=(14, 8))
    fig.suptitle(f'Match Results: {name}', fontsize=18, fontweight='bold')
    
    gs = fig.add_gridspec(2, 2, width_ratios=[2, 1], height_ratios=[1, 1])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[:, 1])

    # Plot cumulative chips (ax1)
    ax1.plot(cumulative_chips, label=f"{agent1_name} vs {agent2_name}", linewidth=2, color='#2563eb')
    ax1.axhline(0, color='#ef4444', linestyle='--', alpha=0.5)
    ax1.set_ylabel(f"Cumulative Chips Gain ({agent1_name})")
    ax1.set_xlabel("Hands Played")
    ax1.set_title("Profit / Loss Over Time")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot Entropy if available (ax2)
    if entropy_history:
        ax2.plot(entropy_history, color='#f59e0b', alpha=0.3, label=f"{agent1_name} Belief Entropy")
        if len(entropy_history) > 20:
            window = min(20, len(entropy_history)//5)
            moving_avg = [sum(entropy_history[max(0, i-window):i+1])/len(entropy_history[max(0, i-window):i+1]) for i in range(len(entropy_history))]
            ax2.plot(moving_avg, color='#ea580c', label='Moving Avg (smooth)', linewidth=2)
        ax2.set_ylabel("Entropy (Uncertainty)")
        ax2.set_xlabel("Action Samples")
        ax2.set_title("Agent Uncertainty Over Time")
        ax2.grid(True, alpha=0.3)
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, "No Entropy Data for this Match", horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
        ax2.set_axis_off()

    # Plot Pie Chart (ax3)
    total = wins1 + wins2 + ties
    if total > 0:
        labels = [f"{agent1_name} Wins", f"{agent2_name} Wins", "Ties"]
        sizes = [wins1, wins2, ties]
        colors = ['#3b82f6', '#ef4444', '#94a3b8']
        
        # Only plot slices that exist
        idx = [i for i, s in enumerate(sizes) if s > 0]
        f_labels = [labels[i] for i in idx]
        f_sizes = [sizes[i] for i in idx]
        f_colors = [colors[i] for i in idx]

        ax3.pie(f_sizes, labels=f_labels, colors=f_colors, autopct='%1.1f%%', startangle=90, shadow=False, textprops={'fontsize': 12, 'fontweight': '500'})
        ax3.set_title("Hand Outcomes", fontsize=14, fontweight='bold')
    else:
        ax3.text(0.5, 0.5, "No Win/Loss Data", horizontalalignment='center', verticalalignment='center', transform=ax3.transAxes)
        ax3.set_axis_off()

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Plot saved to {save_path}")
    else:
        plt.show()

