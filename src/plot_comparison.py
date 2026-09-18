"""
Reads all result CSVs and produces two comparison charts:
1. rider_comparison.png       -> original 2-scenario chart (5 vs 8 riders, no batching)
2. rider_comparison_full.png  -> full 3-scenario chart (baseline, batching, more riders)
"""

import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------
# Load all result sets
# ---------------------------
df_baseline = pd.read_csv("results_5_riders.csv")
df_8riders = pd.read_csv("results_8_riders.csv")
df_batched = pd.read_csv("results_5_riders_batched.csv")


def build_summary(scenarios: dict) -> pd.DataFrame:
    return pd.DataFrame({
        name: [
            df["total_delivery_time"].mean(),
            df["wait_for_rider"].mean(),
            df["met_sla"].mean() * 100,
        ]
        for name, df in scenarios.items()
    }, index=["Avg Delivery Time (min)", "Avg Wait for Rider (min)", "SLA Met Rate (%)"])


def plot_summary(summary: pd.DataFrame, colors: list, save_path: str, title: str):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(title, fontsize=14)

    for ax, metric in zip(axes, summary.index):
        summary.loc[metric].plot(kind="bar", ax=ax, color=colors)
        ax.set_title(metric)
        ax.set_ylabel(metric)
        ax.set_xticklabels(summary.columns, rotation=0, fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.show()
    print(f"Saved chart to {save_path}")


# ---------------------------
# Chart 1: original 2-scenario comparison (5 vs 8 riders)
# ---------------------------
scenarios_basic = {
    "5 riders": df_baseline,
    "8 riders": df_8riders,
}
summary_basic = build_summary(scenarios_basic)
print("=== Rider Count Comparison ===")
print(summary_basic, "\n")
plot_summary(
    summary_basic,
    colors=["#d9534f", "#5cb85c"],
    save_path="results/rider_comparison.png",
    title="Impact of Rider Count on Delivery Performance",
)

# ---------------------------
# Chart 2: full 3-scenario comparison (baseline, batching, more riders)
# ---------------------------
scenarios_full = {
    "5 riders\n(baseline)": df_baseline,
    "5 riders\n+ batching": df_batched,
    "8 riders\n(no batching)": df_8riders,
}
summary_full = build_summary(scenarios_full)
print("=== Full Comparison (incl. batching) ===")
print(summary_full, "\n")
plot_summary(
    summary_full,
    colors=["#d9534f", "#f0ad4e", "#5cb85c"],
    save_path="results/rider_comparison_full.png",
    title="Rider Count vs. Order Batching: Impact on Delivery Performance",
)