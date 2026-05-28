CREATE OR REPLACE VIEW transport.vw_tfi_batch_summary AS
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    status,
    error_message,
    created_at
FROM transport.ingestion_batch
WHERE source_name = 'tfi';


CREATE OR REPLACE VIEW transport.vw_tfi_quality_summary AS
SELECT
    check_id,
    batch_id,
    check_name,
    issue_count,
    status,
    details,
    batch_time,
    created_at
FROM transport.data_quality_checks
WHERE source_name = 'tfi';


CREATE OR REPLACE VIEW transport.vw_tfi_trip_update_detail AS
SELECT
    trip_update_id,
    batch_id,
    entity_id,
    trip_id,
    route_id,
    start_time,
    start_date,
    schedule_relationship,
    vehicle_id,
    stop_sequence,
    stop_id,
    arrival_delay_seconds,
    departure_delay_seconds,
    arrival_time_utc,
    departure_time_utc,
    batch_time,
    created_at,
    CASE
        WHEN trip_id IS NULL OR TRIM(trip_id) = '' THEN 1
        ELSE 0
    END AS missing_trip_id_flag,
    CASE
        WHEN route_id IS NULL OR TRIM(route_id) = '' THEN 1
        ELSE 0
    END AS missing_route_id_flag,
    CASE
        WHEN stop_id IS NULL OR TRIM(stop_id) = '' THEN 1
        ELSE 0
    END AS missing_stop_id_flag
FROM transport.tfi_trip_updates;


CREATE OR REPLACE VIEW transport.vw_tfi_delay_by_route AS
SELECT
    route_id,
    COUNT(*) AS stop_update_count,
    AVG(arrival_delay_seconds) AS avg_arrival_delay_seconds,
    AVG(departure_delay_seconds) AS avg_departure_delay_seconds,
    MAX(arrival_delay_seconds) AS max_arrival_delay_seconds,
    MAX(departure_delay_seconds) AS max_departure_delay_seconds,
    SUM(CASE WHEN arrival_delay_seconds > 300 THEN 1 ELSE 0 END) AS arrivals_over_5_mins_late,
    SUM(CASE WHEN departure_delay_seconds > 300 THEN 1 ELSE 0 END) AS departures_over_5_mins_late
FROM transport.tfi_trip_updates
WHERE route_id IS NOT NULL
  AND TRIM(route_id) <> ''
GROUP BY route_id;


CREATE OR REPLACE VIEW transport.vw_tfi_delay_by_stop AS
SELECT
    stop_id,
    COUNT(*) AS stop_update_count,
    AVG(arrival_delay_seconds) AS avg_arrival_delay_seconds,
    AVG(departure_delay_seconds) AS avg_departure_delay_seconds,
    MAX(arrival_delay_seconds) AS max_arrival_delay_seconds,
    MAX(departure_delay_seconds) AS max_departure_delay_seconds,
    SUM(CASE WHEN arrival_delay_seconds > 300 THEN 1 ELSE 0 END) AS arrivals_over_5_mins_late,
    SUM(CASE WHEN departure_delay_seconds > 300 THEN 1 ELSE 0 END) AS departures_over_5_mins_late
FROM transport.tfi_trip_updates
WHERE stop_id IS NOT NULL
  AND TRIM(stop_id) <> ''
GROUP BY stop_id;


CREATE OR REPLACE VIEW transport.vw_tfi_missing_trip_records AS
SELECT
    trip_update_id,
    batch_id,
    entity_id,
    trip_id,
    route_id,
    start_time,
    start_date,
    vehicle_id,
    stop_sequence,
    stop_id,
    arrival_delay_seconds,
    departure_delay_seconds,
    batch_time
FROM transport.tfi_trip_updates
WHERE trip_id IS NULL
   OR TRIM(trip_id) = '';


CREATE OR REPLACE VIEW transport.vw_tfi_duplicate_trip_stop_time AS
SELECT
    batch_id,
    trip_id,
    stop_id,
    arrival_time_utc,
    departure_time_utc,
    COUNT(*) AS duplicate_count
FROM transport.tfi_trip_updates
GROUP BY
    batch_id,
    trip_id,
    stop_id,
    arrival_time_utc,
    departure_time_utc
HAVING COUNT(*) > 1;


CREATE OR REPLACE VIEW transport.vw_combined_transport_batch_monitor AS
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    status,
    error_message,
    created_at
FROM transport.ingestion_batch;