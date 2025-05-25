import subprocess
import argparse
import re
from pathlib import Path
import threading

skip_current = False
current_proc = None

def listen_for_skip():
    global skip_current, current_proc
    print("Press 's' + Enter at any time to skip the current file.")
    while True:
        user_input = input()
        if user_input.strip().lower() == 's':
            print("Skip request received from keyboard. Attempting to terminate current process...")
            skip_current = True
            if current_proc is not None:
                try:
                    current_proc.terminate()
                except Exception as e:
                    print(f"Failed to terminate process: {e}")

def get_args():
    parser = argparse.ArgumentParser(description="Run ECBS on first N YAML files in each subdirectory. It will skip already existing schedules.")
    parser.add_argument("--inputs_dir", type=str, required=True, help="Directory containing subdirectories with .yaml files")
    parser.add_argument("--n", type=int, default=None, help="Number of .yaml files to process per subdirectory (default: all)")
    parser.add_argument("--ecbs_path", type=str, default="./build/libMultiRobotPlanning/ecbs", help="Path to ECBS binary")
    parser.add_argument("--weight", type=float, default=1.1, help="ECBS weight parameter")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout for each ECBS call in seconds (default: 180 seconds)")
    return parser.parse_args()

def natural_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def main(args):
    global skip_current, current_proc
    # Start the skip listener thread
    threading.Thread(target=listen_for_skip, daemon=True).start()
    for subdir in sorted([d for d in Path(args.inputs_dir).iterdir() if d.is_dir()], key=natural_key):
        yaml_files = sorted(subdir.glob("*.yaml"), key=natural_key)
        if not yaml_files:
            continue
        to_process = yaml_files if args.n is None else yaml_files[:args.n]
        schedules_dir = subdir / "schedules"
        schedules_dir.mkdir(exist_ok=True)
        for yaml_file in to_process:
            if skip_current:
                print(f"Skipping (user request): {yaml_file}")
                skip_current = False
                continue
            out_file = schedules_dir / f"schedule_{yaml_file.name}"
            if out_file.exists():
                print(f"Skipping (already exists): {out_file}")
                continue
            print(f"Scheduling: {yaml_file} -> {out_file}")
            try:
                current_proc = subprocess.Popen([
                    args.ecbs_path,
                    "-i", str(yaml_file),
                    "-o", str(out_file),
                    "-w", str(args.weight)
                ])
                current_proc.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                print(f"Timeout expired for {yaml_file}, skipping.")
                current_proc.terminate()
            except Exception as e:
                print(f"Process error: {e}")
            finally:
                current_proc = None
                if skip_current:
                    print(f"File skipped by user request: {yaml_file}")
                    skip_current = False

if __name__ == "__main__":
    main(get_args())