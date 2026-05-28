import subprocess
import time
from datetime import datetime


PIPELINES = [
    {
        "name": "Irish Rail Current Trains",
        "script": "scripts/load_irish_rail_current_trains.py"
    },
    {
        "name": "TFI TripUpdates",
        "script": "scripts/load_tfi_trip_updates.py"
    }
]

RUN_INTERVAL_SECONDS = 60
TOTAL_RUNS = 2


def run_pipeline(pipeline):
    print("=" * 70)
    print(f"Starting {pipeline['name']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    result = subprocess.run(
        ["python", pipeline["script"]],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print("Errors or warnings:")
        print(result.stderr)

    print(f"Finished {pipeline['name']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    print("Combined transport scheduled ingestion started")
    print(f"Run interval: {RUN_INTERVAL_SECONDS} seconds")
    print(f"Total runs: {TOTAL_RUNS}")

    for run_number in range(1, TOTAL_RUNS + 1):
        print(f"\nCombined run {run_number} of {TOTAL_RUNS}")

        for pipeline in PIPELINES:
            run_pipeline(pipeline)

        if run_number < TOTAL_RUNS:
            print(f"Waiting {RUN_INTERVAL_SECONDS} seconds before next combined run")
            time.sleep(RUN_INTERVAL_SECONDS)

    print("\nCombined transport scheduled ingestion completed")


if __name__ == "__main__":
    main()