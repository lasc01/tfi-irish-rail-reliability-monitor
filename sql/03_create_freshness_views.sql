CREATE OR REPLACE VIEW transport.vw_latest_ingestion_freshness AS
WITH latest_batch AS (
    SELECT
        source_name,
        endpoint_name,
        MAX(batch_time) AS latest_batch_time
    FROM transport.ingestion_batch
    WHERE status = 'success'
    GROUP BY source_name, endpoint_name
)
SELECT
    source_name,
    endpoint_name,
    latest_batch_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - latest_batch_time)) / 60 AS minutes_since_last_success,
    CASE
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - latest_batch_time)) / 60 <= 10 THEN 'fresh'
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - latest_batch_time)) / 60 <= 30 THEN 'warning'
        ELSE 'stale'
    END AS freshness_status
FROM latest_batch;


CREATE OR REPLACE VIEW transport.vw_batch_volume_anomaly AS
WITH batch_stats AS (
    SELECT
        batch_id,
        source_name,
        endpoint_name,
        batch_time,
        record_count,
        AVG(record_count) OVER (
            PARTITION BY source_name, endpoint_name
            ORDER BY batch_time
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS previous_avg_record_count
    FROM transport.ingestion_batch
    WHERE status = 'success'
)
SELECT
    batch_id,
    source_name,
    endpoint_name,
    batch_time,
    record_count,
    previous_avg_record_count,
    record_count - previous_avg_record_count AS record_count_difference,
    CASE
        WHEN previous_avg_record_count IS NULL THEN 'not_enough_history'
        WHEN record_count < previous_avg_record_count * 0.80 THEN 'low_volume_warning'
        WHEN record_count > previous_avg_record_count * 1.20 THEN 'high_volume_warning'
        ELSE 'normal'
    END AS volume_status
FROM batch_stats;


CREATE OR REPLACE VIEW transport.vw_operational_monitoring_summary AS
SELECT
    b.batch_id,
    b.source_name,
    b.endpoint_name,
    b.batch_time,
    b.record_count,
    b.status AS batch_status,
    h.pipeline_health_status,
    f.minutes_since_last_success,
    f.freshness_status,
    v.volume_status,
    v.previous_avg_record_count,
    v.record_count_difference
FROM transport.ingestion_batch b
LEFT JOIN transport.vw_pipeline_health_score h
    ON b.batch_id = h.batch_id
LEFT JOIN transport.vw_latest_ingestion_freshness f
    ON b.source_name = f.source_name
   AND b.endpoint_name = f.endpoint_name
LEFT JOIN transport.vw_batch_volume_anomaly v
    ON b.batch_id = v.batch_id
WHERE b.source_name = 'irish_rail';
