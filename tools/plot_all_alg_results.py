import argparse
import yaml
import matplotlib.pyplot as plt
from pathlib import Path
import math

# Define SI units for known metrics
metric_units = {
    "average_cost": "steps",
    "average_makespan": "steps",
    "average_runtime": "s",
    "average_highLevelExpanded": "nodes",
    "average_lowLevelExpanded": "nodes",
}

def extract_scenario_type(filename: str) -> str:
    # e.g., global_averages_random.yaml -> random
    parts = filename.split('_')
    if len(parts) >= 3:
        return parts[-1].replace('.yaml', '')
    return "unknown"

def load_metrics(analysis_dir: Path, metrics: list, algorithms: list = None) -> dict:
    # {metric: {(algorithm, scenario_type): (x, y)}}
    data = {metric: {} for metric in metrics}
    for alg_dir in analysis_dir.iterdir():
        if not alg_dir.is_dir():
            continue
        algorithm = alg_dir.name
        if algorithms is not None and algorithm not in algorithms:
            continue
        for yaml_file in alg_dir.glob("*.yaml"):
            scenario_type = extract_scenario_type(yaml_file.name)
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)
            agent_counts = []
            metric_values = {metric: [] for metric in metrics}
            for agent_str in sorted(content, key=lambda x: int(x)):
                agent_counts.append(int(agent_str))
                for metric in metrics:
                    metric_val = content[agent_str].get(metric, None)
                    metric_values[metric].append(metric_val)
            for metric in metrics:
                data[metric][(algorithm, scenario_type)] = (agent_counts, metric_values[metric])
    return data

def plot_metrics(data: dict, metrics: list, save_path: Path):
    n_metrics = len(metrics)
    ncols = min(n_metrics, 2)
    nrows = math.ceil(n_metrics / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 6 * nrows), squeeze=False)
    axes = axes.flatten()
    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        for (algorithm, scenario_type), (x, y) in data[metric].items():
            ax.plot(x, y, marker='o', label=f"{algorithm} - {scenario_type}")
        ax.set_xlabel("Number of agents")
        unit = metric_units.get(metric, "")
        ylabel = f"{metric} [{unit}]" if unit else metric
        ax.set_ylabel(ylabel)
        ax.set_title(f"{metric}")
        ax.legend()
        ax.grid(True)
    # Hide unused subplots
    for i in range(len(metrics), len(axes)):
        fig.delaxes(axes[i])
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Plot saved to {save_path}")
    plt.show()
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Plot metrics from YAML files in the analysis directory.")
    parser.add_argument("analysis_dir", type=str, help="Path to the analysis directory containing algorithm subdirectories.")
    parser.add_argument("--metrics", nargs="+", default=["average_cost", "average_makespan"], help="Metrics to plot.")
    parser.add_argument("--algorithms", nargs="+", default=None, help="List of algorithm subdirectory names to plot (default: all).")
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir)
    metrics = args.metrics
    algorithms = args.algorithms

    data = load_metrics(analysis_dir, metrics, algorithms)
    save_file = f"{'_'.join(metrics)}_cross_alg_metrics.png"
    if algorithms is not None:
        save_file = f"{'_'.join(algorithms)}_{save_file}"
    else:
        save_file = f"all_{save_file}"
    save_path = analysis_dir / save_file
    plot_metrics(data, metrics, save_path)

if __name__ == "__main__":
    main()