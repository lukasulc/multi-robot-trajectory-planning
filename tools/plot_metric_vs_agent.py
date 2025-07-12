import argparse
import yaml
import re
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, List, Any, DefaultDict
from calculate_averages import compute_averages, save_global_averages_by_scenario, count_fast_scenarios
from plot_all_alg_results import load_metrics
import numpy as np

ALL_METRICS: List[str] = [
        'cost',
        'makespan',
        'runtime',
        'highLevelExpanded',
        'lowLevelExpanded',
    ]

metric_units = {
    "cost": "steps",
    "makespan": "steps",
    "runtime": "s",
    "highLevelExpanded": "nodes",
    "lowLevelExpanded": "nodes",
}

metric_fitting_degree = {
    "cost": 2,
    "makespan": 2,
}

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

def traverse_subdirs_and_load_metrics(dir_path: Path, metrics: List[str], subdir_path: str) -> Dict[str, DefaultDict[str, DefaultDict[int, List[float]]]]:
    # {scenario_type: {agent_count: [metric_values]}}
    data: Dict[str, DefaultDict[str, DefaultDict[int, List[float]]]] = {
        metric: defaultdict(lambda: defaultdict(list)) for metric in metrics
    }

    for scenario_dir in dir_path.iterdir():
        if not scenario_dir.is_dir() or scenario_dir.name.find("analysis") != -1:
            continue
        print(f"Reading directory: {scenario_dir.name}")
        scenario_type = extract_scenario_type(scenario_dir.name)
        subdir = scenario_dir / subdir_path
        if not subdir.exists():
            print(f"Subdirectory {subdir} does not exist, skipping.")
            continue
        for sched_file in subdir.glob("*_agents.yaml"):
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

def format_polynomial_coef_to_string(coeffs: np.ndarray, degree) -> str:
    terms = []
    for i, c in enumerate(coeffs):
        power = degree - i
        if abs(c) < 1e-4:
            continue
        coeff_str = f"{abs(c):.3g}"
        sign = "-" if c < 0 else "+"
        if not terms:
            sign = "-" if c < 0 else ""
        if power == 0:
            terms.append(f"{sign} {coeff_str}")
        elif power == 1:
            terms.append(f"{sign} {coeff_str}x")
        else:
            terms.append(f"{sign} {coeff_str}x^{power}")
    eqn = " ".join(terms)
    return f"y = {eqn}"

def fit_and_plot_polynomial(ax, x, y, degree=2, color=None):
    if len(x) < degree + 1:
        return  # Not enough points to fit
    coeffs = np.polyfit(x, y, degree)
    poly = np.poly1d(coeffs)
    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = poly(x_fit)
    ax.plot(x_fit, y_fit, '-.', label=format_polynomial_coef_to_string(coeffs, degree=degree), color=color)

def plot_metric_vs_agents(
    avg_dict: Dict[str, Dict[str, Dict[int, float]]],
    output_dir: Path,
    metrics: List[str],
    args: argparse.Namespace
):
    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(8 * n_metrics, 6), squeeze=False)

    color_map = plt.get_cmap("tab20")

    for idx, metric in enumerate(metrics):
        ax = axes[0][idx]
        metric_data = avg_dict[metric]
        for i, (scenario_type, agent_dict) in enumerate(metric_data.items()):
            x = sorted(agent_dict.keys())[:args.cutoff]
            y = [agent_dict[n] for n in x]
            ax.plot(x, y, marker='o', label=f"{output_dir.name} - {scenario_type}", linestyle=':',)
            degree = metric_fitting_degree[metric]
            if metric not in args.skip_fit_metrics and degree:
                fit_and_plot_polynomial(ax, x, y, degree=degree, color=color_map(i*2 + 1))
        ax.set_xlabel("Number of agents")
        unit = metric_units.get(metric, "")
        ax.set_ylabel(f"{metric.capitalize()} [{unit}]" if unit else metric)
        ax.set_title(f"Average {metric} vs. Number of agents")
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    if args.save_results:
        plot_path = output_dir / f"{'_'.join(metrics)}_vs_agents.png"
        plt.savefig(plot_path)
        print(f"Plot saved to {plot_path}")
        return
    plt.show()

def main(args: argparse.Namespace) -> None:
    results_dir: Path = Path(args.results_dir)
    output_dir: Path = Path(args.output_dir)
    metrics: List[str] = args.metrics
    if args.run_compute:
        data = traverse_subdirs_and_load_metrics(results_dir, ALL_METRICS, args.subdir_path)

        avg_dict, meta_dict = compute_averages(data, ALL_METRICS)
        additional_metrics = {}
        additional_metrics['solutions_computed_<1_second'] = count_fast_scenarios(data, threshold=1.0)
        additional_metrics['solutions_computed_<10_seconds'] = count_fast_scenarios(data, threshold=10.0)
        save_global_averages_by_scenario(avg_dict, meta_dict, output_dir, additional_metrics)
        plot_metric_vs_agents(avg_dict, output_dir, metrics, args)
    else:
        avg_dict = load_metrics(output_dir.parent, metrics, algorithms=[output_dir.name], special_format=True)
        plot_metric_vs_agents(avg_dict, output_dir, metrics, args)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot average MAPF metrics vs. number of agents for scenario types.")
    parser.add_argument("results_dir", help="Directory containing scenario subdirectories")
    parser.add_argument("output_dir", type=str, help="Path to save the output plot")
    parser.add_argument("--subdir_path", type=str, default="schedules", help="Path to subdirectory within results_dir (default: schedules)")
    parser.add_argument("--metrics", nargs="+", default=["cost", "makespan"], help="Metrics to plot (default: cost makespan)")
    parser.add_argument("--skip_fit_metrics", nargs="+", default=[], help="Metrics to skip fitting (default: None)")
    parser.add_argument("--save_results", type=bool, default=True, help="Save results to file (default: True)")
    parser.add_argument("--cutoff", type=int, default=30, help="Save results to file (default: 30)")
    parser.add_argument("--run_compute", type=bool, default=True, action=argparse.BooleanOptionalAction, help="Calculate averages or load already calculated (default: True)")
    return parser.parse_args()

if __name__ == "__main__":
    main(get_args())