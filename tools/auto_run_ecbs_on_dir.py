import subprocess
import argparse
import re
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description="Run ECBS on first N YAML files in each subdirectory. It will skip already existing schedules.")
    parser.add_argument("--inputs_dir", type=str, required=True, help="Directory containing subdirectories with .yaml files")
    parser.add_argument("--n", type=int, default=None, help="Number of .yaml files to process per subdirectory (default: all)")
    parser.add_argument("--ecbs_path", type=str, default="./build/libMultiRobotPlanning/ecbs", help="Path to ECBS binary")
    parser.add_argument("--weight", type=float, default=1.1, help="ECBS weight parameter")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout for each ECBS call in seconds (default: 180 seconds)")
    return parser.parse_args()

def natural_key(s):
    # Split string into list of strings and integers for natural sorting
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def main(args):
    for subdir in sorted([d for d in Path(args.inputs_dir).iterdir() if d.is_dir()], key=natural_key):
        yaml_files = sorted(subdir.glob("*.yaml"), key=natural_key)
        if not yaml_files:
            continue
        to_process = yaml_files if args.n is None else yaml_files[:args.n]
        schedules_dir = subdir / "schedules"
        schedules_dir.mkdir(exist_ok=True)
        for yaml_file in to_process:
            out_file = schedules_dir / f"schedule_{yaml_file.name}"
            if out_file.exists():
                print(f"Skipping (already exists): {out_file}")
                continue
            print(f"Scheduling: {yaml_file} -> {out_file}")
            try:
                subprocess.run([
                    args.ecbs_path,
                    "-i", str(yaml_file),
                    "-o", str(out_file),
                    "-w", str(args.weight)
                ], check=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                print(f"Timeout expired for {yaml_file}, skipping.")


if __name__ == "__main__":
    main(get_args())