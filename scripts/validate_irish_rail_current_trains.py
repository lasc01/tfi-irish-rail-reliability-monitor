import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LOG_DIR = Path("logs")

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_current_trains():
    url = "https://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.text


def parse_current_trains(xml_text):
    root = ET.fromstring(xml_text)

    rows = []

    for train in root:
        row = {}
        for child in train:
            tag = child.tag.split("}")[-1]
            row[tag] = child.text
        rows.append(row)

    return pd.DataFrame(rows)


def standardise_columns(df):
    df.columns = [col.strip().lower() for col in df.columns]

    rename_map = {
        "trainstatus": "train_status",
        "trainlatitude": "train_latitude",
        "trainlongitude": "train_longitude",
        "traincode": "train_code",
        "traindate": "train_date",
        "publicmessage": "public_message",
        "direction": "direction"
    }

    df = df.rename(columns=rename_map)

    return df


def run_quality_checks(df, batch_time):
    checks = []

    total_rows = len(df)

    checks.append({
        "batch_time": batch_time,
        "check_name": "total_rows",
        "issue_count": total_rows,
        "status": "info",
        "details": "Total number of train records collected from the API"
    })

    if total_rows == 0:
        checks.append({
            "batch_time": batch_time,
            "check_name": "empty_api_response",
            "issue_count": 1,
            "status": "fail",
            "details": "The API returned zero train records"
        })

        return pd.DataFrame(checks)

    required_columns = [
        "train_code",
        "train_status",
        "train_latitude",
        "train_longitude",
        "train_date",
        "direction"
    ]

    for col in required_columns:
        if col not in df.columns:
            checks.append({
                "batch_time": batch_time,
                "check_name": f"missing_column_{col}",
                "issue_count": 1,
                "status": "fail",
                "details": f"Required column {col} is missing from the API output"
            })

    if "train_code" in df.columns:
        missing_train_code = df["train_code"].isna().sum() + (df["train_code"].astype(str).str.strip() == "").sum()

        checks.append({
            "batch_time": batch_time,
            "check_name": "missing_train_code",
            "issue_count": int(missing_train_code),
            "status": "fail" if missing_train_code > 0 else "pass",
            "details": "Records where train code is missing or blank"
        })

        duplicate_train_code = df.duplicated(subset=["train_code"], keep=False).sum()

        checks.append({
            "batch_time": batch_time,
            "check_name": "duplicate_train_code",
            "issue_count": int(duplicate_train_code),
            "status": "warning" if duplicate_train_code > 0 else "pass",
            "details": "Records where the same train code appears more than once in one API pull"
        })

    if "train_latitude" in df.columns:
        missing_latitude = df["train_latitude"].isna().sum() + (df["train_latitude"].astype(str).str.strip() == "").sum()

        checks.append({
            "batch_time": batch_time,
            "check_name": "missing_train_latitude",
            "issue_count": int(missing_latitude),
            "status": "warning" if missing_latitude > 0 else "pass",
            "details": "Records where train latitude is missing"
        })

    if "train_longitude" in df.columns:
        missing_longitude = df["train_longitude"].isna().sum() + (df["train_longitude"].astype(str).str.strip() == "").sum()

        checks.append({
            "batch_time": batch_time,
            "check_name": "missing_train_longitude",
            "issue_count": int(missing_longitude),
            "status": "warning" if missing_longitude > 0 else "pass",
            "details": "Records where train longitude is missing"
        })

    if "train_status" in df.columns:
        invalid_status = df[
            ~df["train_status"].astype(str).str.lower().isin(["n", "r", "t"])
        ]

        checks.append({
            "batch_time": batch_time,
            "check_name": "unexpected_train_status",
            "issue_count": int(len(invalid_status)),
            "status": "warning" if len(invalid_status) > 0 else "pass",
            "details": "Records where train status is outside expected values"
        })

    return pd.DataFrame(checks)


def main():
    batch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Fetching Irish Rail current train data")

    xml_text = fetch_current_trains()

    raw_file = RAW_DIR / f"irish_rail_current_trains_{file_time}.xml"
    raw_file.write_text(xml_text, encoding="utf-8")

    df = parse_current_trains(xml_text)
    df = standardise_columns(df)

    df["batch_time"] = batch_time

    output_file = PROCESSED_DIR / f"irish_rail_current_trains_clean_{file_time}.csv"
    df.to_csv(output_file, index=False)

    quality_log = run_quality_checks(df, batch_time)

    quality_file = LOG_DIR / f"irish_rail_quality_log_{file_time}.csv"
    quality_log.to_csv(quality_file, index=False)

    print(f"Rows collected: {len(df)}")
    print(f"Raw file saved to: {raw_file}")
    print(f"Clean file saved to: {output_file}")
    print(f"Quality log saved to: {quality_file}")

    print("\nQuality check summary:")
    print(quality_log)


if __name__ == "__main__":
    main()