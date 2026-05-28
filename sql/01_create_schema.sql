CREATE SCHEMA IF NOT EXISTS transport;

CREATE TABLE IF NOT EXISTS transport.ingestion_batch (
    batch_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    endpoint_name VARCHAR(150) NOT NULL,
    batch_time TIMESTAMP NOT NULL,
    raw_file_path TEXT,
    processed_file_path TEXT,
    record_count INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transport.irish_rail_current_trains (
    snapshot_id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES transport.ingestion_batch(batch_id),
    train_status VARCHAR(50),
    train_latitude NUMERIC(10, 6),
    train_longitude NUMERIC(10, 6),
    train_code VARCHAR(50),
    train_date VARCHAR(50),
    public_message TEXT,
    direction VARCHAR(100),
    batch_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transport.data_quality_checks (
    check_id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES transport.ingestion_batch(batch_id),
    source_name VARCHAR(100),
    check_name VARCHAR(150),
    issue_count INTEGER,
    status VARCHAR(50),
    details TEXT,
    batch_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);