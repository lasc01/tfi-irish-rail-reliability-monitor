CREATE OR REPLACE VIEW transport.vw_ingestion_batch_summary AS
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    status,
    error_message,
    raw_file_path,
    processed_file_path,
    created_at
FROM transport.ingestion_batch;


CREATE OR REPLACE VIEW transport.vw_quality_check_summary AS
SELECT
    check_id,
    batch_id,
    source_name,
    check_name,
    issue_count,
    status,
    details,
    batch_time,
    created_at
FROM transport.data_quality_checks;


CREATE OR REPLACE VIEW transport.vw_latest_quality_status AS
WITH latest_batch AS (
    SELECT MAX(batch_id) AS batch_id
    FROM transport.ingestion_batch
    WHERE source_name = 'irish_rail'
)
SELECT
    q.batch_id,
    q.source_name,
    q.check_name,
    q.issue_count,
    q.status,
    q.details,
    q.batch_time
FROM transport.data_quality_checks q
JOIN latest_batch lb
    ON q.batch_id = lb.batch_id;


CREATE OR REPLACE VIEW transport.vw_batch_record_trend AS
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    status
FROM transport.ingestion_batch
WHERE source_name = 'irish_rail'
ORDER BY batch_time;


CREATE OR REPLACE VIEW transport.vw_train_snapshot_detail AS
SELECT
    snapshot_id,
    batch_id,
    train_code,
    train_status,
    train_latitude,
    train_longitude,
    train_date,
    direction,
    public_message,
    batch_time,
    created_at,
    CASE
        WHEN train_latitude IS NULL OR train_longitude IS NULL THEN 1
        ELSE 0
    END AS missing_coordinate_flag
FROM transport.irish_rail_current_trains;


CREATE OR REPLACE VIEW transport.vw_missing_coordinate_records AS
SELECT
    snapshot_id,
    batch_id,
    train_code,
    train_status,
    train_latitude,
    train_longitude,
    train_date,
    direction,
    public_message,
    batch_time
FROM transport.irish_rail_current_trains
WHERE train_latitude IS NULL
   OR train_longitude IS NULL;


CREATE OR REPLACE VIEW transport.vw_duplicate_train_codes AS
SELECT
    batch_id,
    train_code,
    COUNT(*) AS duplicate_count
FROM transport.irish_rail_current_trains
WHERE train_code IS NOT NULL
GROUP BY batch_id, train_code
HAVING COUNT(*) > 1;


CREATE OR REPLACE VIEW transport.vw_pipeline_health_score AS
SELECT
    b.batch_id,
    b.source_name,
    b.endpoint_name,
    b.batch_time,
    b.record_count,
    b.status AS batch_status,
    COUNT(q.check_id) AS total_checks,
    SUM(CASE WHEN q.status = 'pass' THEN 1 ELSE 0 END) AS passed_checks,
    SUM(CASE WHEN q.status = 'warning' THEN 1 ELSE 0 END) AS warning_checks,
    SUM(CASE WHEN q.status = 'fail' THEN 1 ELSE 0 END) AS failed_checks,
    CASE
        WHEN SUM(CASE WHEN q.status = 'fail' THEN 1 ELSE 0 END) > 0 THEN 'red'
        WHEN SUM(CASE WHEN q.status = 'warning' THEN 1 ELSE 0 END) > 0 THEN 'amber'
        ELSE 'green'
    END AS pipeline_health_status
FROM transport.ingestion_batch b
LEFT JOIN transport.data_quality_checks q
    ON b.batch_id = q.batch_id
WHERE b.source_name = 'irish_rail'
GROUP BY
    b.batch_id,
    b.source_name,
    b.endpoint_name,
    b.batch_time,
    b.record_count,
    b.status;