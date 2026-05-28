CREATE OR REPLACE VIEW transport.vw_dashboard_overview_kpis AS
SELECT
    COUNT(*) AS total_batches,
    SUM(record_count) AS total_records_processed,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_batches,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_batches,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS batch_success_rate_percent,
    MAX(batch_time) AS latest_batch_time
FROM transport.ingestion_batch;


CREATE OR REPLACE VIEW transport.vw_dashboard_source_summary AS
SELECT
    source_name,
    endpoint_name,
    COUNT(*) AS total_batches,
    SUM(record_count) AS total_records_processed,
    AVG(record_count) AS avg_records_per_batch,
    MIN(record_count) AS min_records_per_batch,
    MAX(record_count) AS max_records_per_batch,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_batches,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_batches,
    MAX(batch_time) AS latest_batch_time
FROM transport.ingestion_batch
GROUP BY source_name, endpoint_name;


CREATE OR REPLACE VIEW transport.vw_dashboard_quality_issue_summary AS
SELECT
    source_name,
    check_name,
    status,
    COUNT(*) AS check_runs,
    SUM(issue_count) AS total_issue_count,
    AVG(issue_count) AS avg_issue_count,
    MAX(issue_count) AS max_issue_count,
    MAX(batch_time) AS latest_check_time
FROM transport.data_quality_checks
WHERE status IN ('warning', 'fail')
GROUP BY source_name, check_name, status;


CREATE OR REPLACE VIEW transport.vw_dashboard_tfi_route_delay_rank AS
SELECT
    route_id,
    stop_update_count,
    ROUND(avg_arrival_delay_seconds::numeric, 2) AS avg_arrival_delay_seconds,
    ROUND((avg_arrival_delay_seconds / 60.0)::numeric, 2) AS avg_arrival_delay_minutes,
    ROUND(avg_departure_delay_seconds::numeric, 2) AS avg_departure_delay_seconds,
    ROUND((avg_departure_delay_seconds / 60.0)::numeric, 2) AS avg_departure_delay_minutes,
    max_arrival_delay_seconds,
    max_departure_delay_seconds,
    arrivals_over_5_mins_late,
    departures_over_5_mins_late
FROM transport.vw_tfi_delay_by_route
WHERE stop_update_count >= 10;


CREATE OR REPLACE VIEW transport.vw_dashboard_tfi_stop_delay_rank AS
SELECT
    stop_id,
    stop_update_count,
    ROUND(avg_arrival_delay_seconds::numeric, 2) AS avg_arrival_delay_seconds,
    ROUND((avg_arrival_delay_seconds / 60.0)::numeric, 2) AS avg_arrival_delay_minutes,
    ROUND(avg_departure_delay_seconds::numeric, 2) AS avg_departure_delay_seconds,
    ROUND((avg_departure_delay_seconds / 60.0)::numeric, 2) AS avg_departure_delay_minutes,
    max_arrival_delay_seconds,
    max_departure_delay_seconds,
    arrivals_over_5_mins_late,
    departures_over_5_mins_late
FROM transport.vw_tfi_delay_by_stop
WHERE stop_update_count >= 10;


CREATE OR REPLACE VIEW transport.vw_dashboard_irish_rail_batch_trend AS
SELECT
    batch_id,
    batch_time,
    record_count,
    status,
    endpoint_name
FROM transport.ingestion_batch
WHERE source_name = 'irish_rail';


CREATE OR REPLACE VIEW transport.vw_dashboard_combined_batch_trend AS
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    status,
    error_message
FROM transport.ingestion_batch;


CREATE OR REPLACE VIEW transport.vw_dashboard_quality_timeline AS
SELECT
    q.batch_id,
    q.source_name,
    b.endpoint_name,
    q.check_name,
    q.status,
    q.issue_count,
    q.batch_time
FROM transport.data_quality_checks q
LEFT JOIN transport.ingestion_batch b
    ON q.batch_id = b.batch_id;


CREATE OR REPLACE VIEW transport.vw_dashboard_tfi_trip_quality_flags AS
SELECT
    batch_id,
    COUNT(*) AS total_trip_update_rows,
    SUM(missing_trip_id_flag) AS missing_trip_id_rows,
    SUM(missing_route_id_flag) AS missing_route_id_rows,
    SUM(missing_stop_id_flag) AS missing_stop_id_rows,
    ROUND(
        100.0 * SUM(missing_trip_id_flag) / COUNT(*),
        2
    ) AS missing_trip_id_percent
FROM transport.vw_tfi_trip_update_detail
GROUP BY batch_id;