import yaml
from typing import Dict, List, Any, Tuple

def compute_averages(
    data: Dict[str, Dict[str, Dict[int, List[float]]]],
    metrics: List[str]
) -> Tuple[
    Dict[str, Dict[str, Dict[int, float]]],
    Dict[str, Dict[str, Dict[str, Any]]]
]:
    """
    Returns:
        avg_dict: {metric: {scenario_type: {agent_count: float}}}
        meta_dict: {metric: {scenario_type: {average_metric: float, max_agent_count: int, num_agent_counts: int}}}
    """
    avg_dict: Dict[str, Dict[str, Dict[int, float]]] = {metric: {} for metric in metrics}
    meta_dict: Dict[str, Dict[str, Dict[str, Any]]] = {metric: {} for metric in metrics}
    for metric in metrics:
        for scenario_type, agent_dict in data[metric].items():
            avg_dict[metric][scenario_type] = {}
            all_values: List[float] = []
            num_scenarios_per_agent: Dict[int, int] = {}
            for agent_count, values in agent_dict.items():
                if values:
                    avg = sum(values) / len(values)
                    avg_dict[metric][scenario_type][agent_count] = avg
                    all_values.extend(values)
                    num_scenarios_per_agent[agent_count] = len(values)
            meta_dict[metric][scenario_type] = {
                f"average_{metric}": sum(all_values) / len(all_values) if all_values else None,
                "num_scenarios_per_agent": num_scenarios_per_agent
            }
    return avg_dict, meta_dict

def save_global_averages_by_scenario(
    avg_dict: Dict[str, Dict[str, Dict[int, float]]],
    meta_dict: Dict[str, Dict[str, Dict[str, Any]]],
    results_dir: Any,
    additional_metrics: Dict[str, Dict[str, Dict[int, int]]]
) -> None:
    for scenario_type in next(iter(avg_dict.values())).keys():
        out: Dict[int, Dict[str, Any]] = {}
        # Collect all agent counts for this scenario type
        agent_counts = set()
        for metric in avg_dict:
            agent_counts.update(avg_dict[metric][scenario_type].keys())
        for agent_count in sorted(agent_counts):
            out[agent_count] = {}
            for additional_metric, metric_data in additional_metrics.items():
                out[agent_count][additional_metric] = metric_data[scenario_type].get(agent_count, 0)
            for metric in avg_dict:
                avg = avg_dict[metric][scenario_type].get(agent_count, None)
                out[agent_count][f"average_{metric}"] = avg
                # Get num_scenarios from meta_dict
                num_scenarios = meta_dict[metric][scenario_type]["num_scenarios_per_agent"].get(agent_count, 0)
                out[agent_count]["num_scenarios"] = num_scenarios
        avg_path = results_dir / f"global_averages_{scenario_type}.yaml"
        with open(avg_path, "w") as f:
            yaml.dump(out, f)
        print(f"Global averages for scenario '{scenario_type}' saved to {avg_path}")

def count_fast_scenarios(
    data: Dict[str, Dict[str, Dict[int, List[float]]]],
    threshold: float = 1.0
) -> Dict[str, Dict[str, Dict[int, int]]]:
    """
    Returns:
        fast_count: {metric: {scenario_type: {agent_count: count}}}
    """
    fast_count: Dict[str, Dict[str, Dict[int, int]]] = {}
    metric = "runtime"
    fast_count = {}
    for scenario_type, agent_dict in data[metric].items():
        fast_count[scenario_type] = {}
        for agent_count, runtimes in agent_dict.items():
            count = sum(1 for rt in runtimes if rt < threshold)
            fast_count[scenario_type][agent_count] = count
    return fast_count