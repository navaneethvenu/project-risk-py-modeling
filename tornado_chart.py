import matplotlib.pyplot as plt
import numpy as np


def tornado_chart_centered(labels, values, title="Tornado Diagram"):
    # Sort by absolute value descending
    sorted_indices = np.argsort(np.abs(values))[::-1]
    labels = [labels[i] for i in sorted_indices]
    values = [values[i] for i in sorted_indices]

    y_pos = np.arange(len(labels))

    color = "#4e79a7"

    fig, ax = plt.subplots(figsize=(8, 5))

    # Draw bars centered on 0
    for i, v in enumerate(values):
        ax.barh(y_pos[i], v, color=color, edgecolor="black")
        align = "left" if v >= 0 else "right"
        offset = 1 if v >= 0 else -1
        ax.text(v + offset, y_pos[i], f"{v:.2f}", va="center", ha=align, fontsize=10)

    # Vertical centerline at 0
    ax.axvline(0, color="black", linewidth=1)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # Top-down biggest to smallest
    ax.set_xlabel("Impact Value")
    ax.set_title(title, fontsize=14)

    # Clean style
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    # plt.show()

    return
