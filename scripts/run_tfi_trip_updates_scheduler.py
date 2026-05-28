import subprocess
import time
from datetime import datetime


SCRIPT_PATH = "scripts/load_tfi_trip_updates.py"

RUN_INTERVAL_SECONDS = 300
TOTAL_RUNS = 12


def run_ingestion():
    print("=" * 70)
    print(f"Starting TFI TripUpdates ingestion at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    result = subprocess.run(
        ["python", SCRIPT_PATH],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print("Errors or warnings:")
        print(result.stderr)

    print(f"Finished TFI TripUpdates ingestion at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    print("TFI TripUpdates scheduled ingestion started")
    print(f"Run interval: {RUN_INTERVAL_SECONDS} seconds")
    print(f"Total runs: {TOTAL_RUNS}")

    for run_number in range(1, TOTAL_RUNS + 1):
        print(f"\nRun {run_number} of {TOTAL_RUNS}")
        run_ingestion()

        if run_number < TOTAL_RUNS:
            print(f"Waiting {RUN_INTERVAL_SECONDS} seconds before next run")
            time.sleep(RUN_INTERVAL_SECONDS)

    print("\nTFI scheduled ingestion completed")


if __name__ == "__main__":
    main()