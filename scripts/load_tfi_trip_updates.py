import os
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
from sqlalchemy import text

from db_connection import get_engine


load_dotenv()


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LOG_DIR = Path("logs")

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_tfi_feed():
    api_key = os.getenv("TFI_API_KEY")
    url = os.getenv("TFI_GTFSR_URL")

    if not api_key:
        raise ValueError("TFI_API_KEY is missing from .env")

    if not url:
        raise ValueError("TFI_GTFSR_URL is missing from .env")

    headers = {
        "x-api-key": api_key
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.content


def parse_trip_updates(feed_content):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(feed_content)

    rows = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update

        trip_id = trip_update.trip.trip_id
        route_id = trip_update.trip.route_id
        start_time = trip_update.trip.start_time
        start_date = trip_update.trip.start_date
        schedule_relationship = str(trip_update.trip.schedule_relationship)
        vehicle_id = trip_update.vehicle.id

        for stop_update in trip_update.stop_time_update:
            row = {
                "entity_id": entity.id,
                "trip_id": trip_id,
                "route_id": route_id,
                "start_time": start_time,
                "start_date": start_date,
                "schedule_relationship": schedule_relationship,
                "vehicle_id": vehicle_id,
                "stop_sequence": stop_update.stop_sequence,
                "stop_id": stop_update.stop_id,
                "arrival_delay_seconds": stop_update.arrival.delay if stop_update.HasField("arrival") else None,
                "arrival_time_utc": stop_update.arrival.time if stop_update.HasField("arrival") else None,
                "departure_delay_seconds": stop_update.departure.delay if stop_update.HasField("departure") else None,
                "departure_time_utc": stop_update.departure.time if stop_update.HasField("departure") else None
            }

            rows.append(row)

    return pd.DataFrame(rows)


def run_quality_checks(df, batch_time):
    checks = []

    total_rows = len(df)

    checks.append({
        "source_name": "tfi",
        "check_name": "total_rows",
        "issue_count": total_rows,
        "status": "info",
        "details": "Total number of TFI trip update stop records collected from the API",
        "batch_time": batch_time
    })

    if total_rows == 0:
        checks.append({
            "source_name": "tfi",
            "check_name": "empty_feed_response",
            "issue_count": 1,
            "status": "fail",
            "details": "The TFI feed returned zero trip update stop records",
            "batch_time": batch_time
        })

        return pd.DataFrame(checks)

    fields_to_check = [
        "trip_id",
        "route_id",
        "stop_id"
    ]

    for field in fields_to_check:
        missing_count = df[field].isna().sum() + (
            df[field].astype(str).str.strip() == ""
        ).sum()

        checks.append({
            "source_name": "tfi",
            "check_name": f"missing_{field}",
            "issue_count": int(missing_count),
            "status": "warning" if missing_count > 0 else "pass",
            "details": f"Records where {field} is missing or blank",
            "batch_time": batch_time
        })

    duplicate_count = df.duplicated(
        subset=["trip_id", "stop_id", "arrival_time_utc", "departure_time_utc"],
        keep=False
    ).sum()

    checks.append({
        "source_name": "tfi",
        "check_name": "duplicate_trip_stop_time",
        "issue_count": int(duplicate_count),
        "status": "warning" if duplicate_count > 0 else "pass",
        "details": "Records where trip, stop, arrival time and departure time appear more than once in one batch",
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
                "raw_file_path": str(raw_file_path) if raw_file_path else None,
                "processed_file_path": str(processed_file_path) if processed_file_path else None,
                "record_count": record_count,
                "status": status,
                "error_message": error_message
            }
        ).scalar()

    return batch_id


def load_trip_updates(engine, df, batch_id, batch_time):
    if df.empty:
        return

    df_to_load = df.copy()
    df_to_load["batch_id"] = batch_id
    df_to_load["batch_time"] = batch_time

    ordered_columns = [
        "batch_id",
        "entity_id",
        "trip_id",
        "route_id",
        "start_time",
        "start_date",
        "schedule_relationship",
        "vehicle_id",
        "stop_sequence",
        "stop_id",
        "arrival_delay_seconds",
        "arrival_time_utc",
        "departure_delay_seconds",
        "departure_time_utc",
        "batch_time"
    ]

    df_to_load = df_to_load[ordered_columns]

    df_to_load.to_sql(
        "tfi_trip_updates",
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

    print("Fetching TFI TripUpdates feed")

    try:
        feed_content = fetch_tfi_feed()

        raw_file = RAW_DIR / f"tfi_trip_updates_{file_time}.pb"
        raw_file.write_bytes(feed_content)

        df = parse_trip_updates(feed_content)

        processed_file = PROCESSED_DIR / f"tfi_trip_updates_clean_{file_time}.csv"
        df.to_csv(processed_file, index=False)

        quality_df = run_quality_checks(df, batch_time)

        quality_file = LOG_DIR / f"tfi_trip_updates_quality_log_{file_time}.csv"
        quality_df.to_csv(quality_file, index=False)

        batch_id = insert_ingestion_batch(
            engine=engine,
            source_name="tfi",
            endpoint_name="gtfsr_v2_trip_updates",
            batch_time=batch_time,
            raw_file_path=raw_file,
            processed_file_path=processed_file,
            record_count=len(df),
            status="success"
        )

        load_trip_updates(engine, df, batch_id, batch_time)
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
            source_name="tfi",
            endpoint_name="gtfsr_v2_trip_updates",
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