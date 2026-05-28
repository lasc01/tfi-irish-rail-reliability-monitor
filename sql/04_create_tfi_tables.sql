CREATE TABLE IF NOT EXISTS transport.tfi_vehicle_positions (
    vehicle_position_id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES transport.ingestion_batch(batch_id),
    entity_id TEXT,
    trip_id TEXT,
    route_id TEXT,
    start_time TEXT,
    start_date TEXT,
    schedule_relationship TEXT,
    vehicle_id TEXT,
    vehicle_label TEXT,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    bearing NUMERIC(10, 2),
    speed NUMERIC(10, 2),
    timestamp_utc BIGINT,
    current_stop_sequence INTEGER,
    stop_id TEXT,
    current_status TEXT,
    congestion_level TEXT,
    occupancy_status TEXT,
    batch_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS transport.tfi_trip_updates (
    trip_update_id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES transport.ingestion_batch(batch_id),
    entity_id TEXT,
    trip_id TEXT,
    route_id TEXT,
    start_time TEXT,
    start_date TEXT,
    schedule_relationship TEXT,
    vehicle_id TEXT,
    stop_sequence INTEGER,
    stop_id TEXT,
    arrival_delay_seconds INTEGER,
    arrival_time_utc BIGINT,
    departure_delay_seconds INTEGER,
    departure_time_utc BIGINT,
    batch_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS transport.tfi_service_alerts (
    service_alert_id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES transport.ingestion_batch(batch_id),
    entity_id TEXT,
    cause TEXT,
    effect TEXT,
    active_start_utc BIGINT,
    active_end_utc BIGINT,
    route_id TEXT,
    stop_id TEXT,
    trip_id TEXT,
    header_text TEXT,
    description_text TEXT,
    url TEXT,
    batch_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);