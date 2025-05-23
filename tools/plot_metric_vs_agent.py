import argparse
import yaml
import re
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, List, Any, DefaultDict
from calculate_averages import compute_averages, save_global_averages_by_scenario

ALL_METRICS: List[str] = [
        'cost',
        'makespan',
        'runtime',
        'highLevelExpanded',
        'lowLevelExpanded',
    ]

def extract_agent_count(filename: str) -> int | None:
    # Assumes filename like schedule_inputs_10_agents.yaml
    match = re.search(r'_(\d+)_agents', filename)
    return int(match.group(1)) if match else None

def extract_scenario_type(dirname: str) -> str:
    # Assumes dirname like random-1, even-2, etc.
    return dirname.split('-')[0]

def read_first_n_lines(file_path: Path, n: int = 6) -> str:
    with open(file_path, 'r') as f:
        lines = [next(f) for _ in range(n)]
    return "".join(lines)

def load_metrics(dir_path: Path, metrics: List[str]) -> Dict[str, DefaultDict[str, DefaultDict[int, List[float]]]]:
    # {scenario_type: {agent_count: [metric_values]}}
    data: Dict[str, DefaultDict[str, DefaultDict[int, List[float]]]] = {
        metric: defaultdict(lambda: defaultdict(list)) for metric in metrics
    }

    for scenario_dir in dir_path.iterdir():
        if not scenario_dir.is_dir():
            continue
        print(f"Reading directory: {scenario_dir.name}")
        scenario_type = extract_scenario_type(scenario_dir.name)
        for sched_file in scenario_dir.glob("schedules/schedule_inputs_*_agents.yaml"):
            agent_count = extract_agent_count(sched_file.name)
            if agent_count is None:
                continue
            try:
                sched_data: dict[str, Any] = yaml.safe_load(read_first_n_lines(sched_file))
                for metric in metrics:
                    metric_val = sched_data.get("statistics", {}).get(metric, None)
                    if metric_val is not None:
                        data[metric][scenario_type][agent_count].append(metric_val)
            except Exception as e:
                print(f"Error reading {sched_file}: {e}")
    return data

def main(args: argparse.Namespace) -> None:
    results_dir: Path = Path(args.results_dir)
    metrics: List[str] = args.metrics
    data = load_metrics(results_dir, ALL_METRICS)

    avg_dict, meta_dict = compute_averages(data, ALL_METRICS)
    save_global_averages_by_scenario(avg_dict, meta_dict, results_dir)

    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(8 * n_metrics, 6), squeeze=False)
    axes = axes[0]  # flatten to 1D

    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        metric_data = avg_dict[metric]
        for scenario_type, agent_dict in metric_data.items():
            x = sorted(agent_dict.keys())
            y = [agent_dict[n] for n in x]
            ax.plot(x, y, marker='o', label=scenario_type)
        ax.set_xlabel("Number of agents")
        ax.set_ylabel(metric.capitalize())
        ax.set_title(f"Average {metric} vs. Number of agents")
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    if args.save_results:
        plot_path = results_dir / f"{'_'.join(metrics)}_vs_agents.png"
        plt.savefig(plot_path)
        print(f"Plot saved to {plot_path}")
        return
    plt.show()

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot average MAPF metrics vs. number of agents for scenario types.")
    parser.add_argument("results_dir", help="Directory containing scenario subdirectories")
    parser.add_argument("--metrics", nargs="+", default=["cost", "makespan"], help="Metrics to plot (default: cost makespan)")
    parser.add_argument("--save_results", type=bool, default=True, help="Save results to file (default: True)")
    return parser.parse_args()

if __name__ == "__main__":
    main(get_args())