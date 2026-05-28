import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from sqlalchemy import text

from db_connection import get_engine


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

    expected_columns = [
        "train_status",
        "train_latitude",
        "train_longitude",
        "train_code",
        "train_date",
        "public_message",
        "direction"
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    df = df[expected_columns]

    df["train_latitude"] = pd.to_numeric(df["train_latitude"], errors="coerce")
    df["train_longitude"] = pd.to_numeric(df["train_longitude"], errors="coerce")

    return df


def run_quality_checks(df, batch_time):
    checks = []

    total_rows = len(df)

    checks.append({
        "source_name": "irish_rail",
        "check_name": "total_rows",
        "issue_count": total_rows,
        "status": "info",
        "details": "Total number of train records collected from the API",
        "batch_time": batch_time
    })

    if total_rows == 0:
        checks.append({
            "source_name": "irish_rail",
            "check_name": "empty_api_response",
            "issue_count": 1,
            "status": "fail",
            "details": "The API returned zero train records",
            "batch_time": batch_time
        })

        return pd.DataFrame(checks)

    missing_train_code = df["train_code"].isna().sum() + (
        df["train_code"].astype(str).str.strip() == ""
    ).sum()

    checks.append({
        "source_name": "irish_rail",
        "check_name": "missing_train_code",
        "issue_count": int(missing_train_code),
        "status": "fail" if missing_train_code > 0 else "pass",
        "details": "Records where train code is missing or blank",
        "batch_time": batch_time
    })

    duplicate_train_code = df.duplicated(subset=["train_code"], keep=False).sum()

    checks.append({
        "source_name": "irish_rail",
        "check_name": "duplicate_train_code",
        "issue_count": int(duplicate_train_code),
        "status": "warning" if duplicate_train_code > 0 else "pass",
        "details": "Records where the same train code appears more than once in one API pull",
        "batch_time": batch_time
    })

    missing_latitude = df["train_latitude"].isna().sum()

    checks.append({
        "source_name": "irish_rail",
        "check_name": "missing_train_latitude",
        "issue_count": int(missing_latitude),
        "status": "warning" if missing_latitude > 0 else "pass",
        "details": "Records where train latitude is missing",
        "batch_time": batch_time
    })

    missing_longitude = df["train_longitude"].isna().sum()

    checks.append({
        "source_name": "irish_rail",
        "check_name": "missing_train_longitude",
        "issue_count": int(missing_longitude),
        "status": "warning" if missing_longitude > 0 else "pass",
        "details": "Records where train longitude is missing",
        "batch_time": batch_time
    })

    valid_status_values = ["n", "r", "t"]

    unexpected_status = df[
        ~df["train_status"].astype(str).str.lower().isin(valid_status_values)
    ]

    checks.append({
        "source_name": "irish_rail",
        "check_name": "unexpected_train_status",
        "issue_count": int(len(unexpected_status)),
        "status": "warning" if len(unexpected_status) > 0 else "pass",
        "details": "Records where train status is outside expected values",
        "batch_time": batch_time
    })

    return pd.DataFrame(checks)


def insert_ingestion_batch(
    engine,
    source_name,
    endpoint_name,
    batch_time,
    raw_file_path,
    processed_file_path,
    record_count,
    status,
    error_message=None
):
    query = text("""
        INSERT INTO transport.ingestion_batch (
            source_name,
            endpoint_name,
            batch_time,
            raw_file_path,
            processed_file_path,
            record_count,
            status,
            error_message
        )
        VALUES (
            :source_name,
            :endpoint_name,
            :batch_time,
            :raw_file_path,
            :processed_file_path,
            :record_count,
            :status,
            :error_message
        )
        RETURNING batch_id;
    """)

    with engine.begin() as conn:
        batch_id = conn.execute(
            query,
            {
                "source_name": source_name,
                "endpoint_name": endpoint_name,
                "batch_time": batch_time,
                "raw_file_path": str(raw_file_path),
                "processed_file_path": str(processed_file_path),
                "record_count": record_count,
                "status": status,
                "error_message": error_message
            }
        ).scalar()

    return batch_id


def load_train_records(engine, df, batch_id, batch_time):
    if df.empty:
        return

    df_to_load = df.copy()
    df_to_load["batch_id"] = batch_id
    df_to_load["batch_time"] = batch_time

    ordered_columns = [
        "batch_id",
        "train_status",
        "train_latitude",
        "train_longitude",
        "train_code",
        "train_date",
        "public_message",
        "direction",
        "batch_time"
    ]

    df_to_load = df_to_load[ordered_columns]

    df_to_load.to_sql(
        "irish_rail_current_trains",
        engine,
        schema="transport",
        if_exists="append",
        index=False
    )


def load_quality_checks(engine, quality_df, batch_id):
    if quality_df.empty:
        return

    quality_to_load = quality_df.copy()
    quality_to_load["batch_id"] = batch_id

    ordered_columns = [
        "batch_id",
        "source_name",
        "check_name",
        "issue_count",
        "status",
        "details",
        "batch_time"
    ]

    quality_to_load = quality_to_load[ordered_columns]

    quality_to_load.to_sql(
        "data_quality_checks",
        engine,
        schema="transport",
        if_exists="append",
        index=False
    )


def main():
    batch_time = datetime.now().replace(microsecond=0)
    file_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    engine = get_engine()

    print("Fetching Irish Rail current train data")

    try:
        xml_text = fetch_current_trains()

        raw_file = RAW_DIR / f"irish_rail_current_trains_{file_time}.xml"
        raw_file.write_text(xml_text, encoding="utf-8")

        df = parse_current_trains(xml_text)
        df = standardise_columns(df)

        processed_file = PROCESSED_DIR / f"irish_rail_current_trains_clean_{file_time}.csv"
        df.to_csv(processed_file, index=False)

        quality_df = run_quality_checks(df, batch_time)

        quality_file = LOG_DIR / f"irish_rail_quality_log_{file_time}.csv"
        quality_df.to_csv(quality_file, index=False)

        batch_id = insert_ingestion_batch(
            engine=engine,
            source_name="irish_rail",
            endpoint_name="getCurrentTrainsXML",
            batch_time=batch_time,
            raw_file_path=raw_file,
            processed_file_path=processed_file,
            record_count=len(df),
            status="success"
        )

        load_train_records(engine, df, batch_id, batch_time)
        load_quality_checks(engine, quality_df, batch_id)

        print(f"Batch loaded successfully. Batch ID: {batch_id}")
        print(f"Rows collected: {len(df)}")
        print(f"Raw file saved to: {raw_file}")
        print(f"Processed file saved to: {processed_file}")
        print(f"Quality log saved to: {quality_file}")

        print("\nQuality check summary:")
        print(quality_df)

    except Exception as error:
        batch_id = insert_ingestion_batch(
            engine=engine,
            source_name="irish_rail",
            endpoint_name="getCurrentTrainsXML",
            batch_time=batch_time,
            raw_file_path=None,
            processed_file_path=None,
            record_count=0,
            status="failed",
            error_message=str(error)
        )

        print(f"Batch failed. Failure logged with Batch ID: {batch_id}")
        print(f"Error: {error}")


if __name__ == "__main__":
    main()