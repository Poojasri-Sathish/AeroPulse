import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "aeropulse.db"

def get_connection():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS airfare_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observation_id TEXT UNIQUE,
        origin_code TEXT NOT NULL,
        origin_city TEXT NOT NULL,
        destination_code TEXT NOT NULL,
        destination_city TEXT NOT NULL,
        route_key TEXT NOT NULL,
        airline_code TEXT NOT NULL,
        airline_name TEXT NOT NULL,
        flight_number TEXT NOT NULL,
        flight_date TEXT NOT NULL,
        collection_timestamp TEXT NOT NULL,
        advance_window_days INTEGER NOT NULL,
        advance_window_tier TEXT NOT NULL,
        fare_class TEXT NOT NULL,
        base_fare REAL NOT NULL,
        taxes REAL NOT NULL,
        airport_fees REAL NOT NULL,
        convenience_fee REAL NOT NULL,
        total_fare REAL NOT NULL,
        data_source TEXT NOT NULL,
        is_clean INTEGER DEFAULT 1,
        quality_flags TEXT,
        is_high_demand_period INTEGER DEFAULT 0,
        demand_period_name TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_index_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        index_date TEXT NOT NULL,
        base_period_label TEXT NOT NULL,
        base_avg_fare REAL NOT NULL,
        current_avg_fare REAL NOT NULL,
        airfare_index REAL NOT NULL,
        previous_index REAL NOT NULL,
        percentage_change REAL NOT NULL,
        total_observations INTEGER NOT NULL,
        active_routes_count INTEGER NOT NULL,
        active_airlines_count INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_spike_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT UNIQUE,
        route_key TEXT NOT NULL,
        origin_city TEXT NOT NULL,
        destination_city TEXT NOT NULL,
        airline_name TEXT NOT NULL,
        flight_date TEXT NOT NULL,
        advance_window_tier TEXT NOT NULL,
        baseline_fare REAL NOT NULL,
        current_fare REAL NOT NULL,
        percentage_change REAL NOT NULL,
        z_score REAL NOT NULL,
        severity TEXT NOT NULL,
        primary_reason TEXT NOT NULL,
        explanation_details TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        status TEXT DEFAULT 'Active'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_quality_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT UNIQUE,
        batch_timestamp TEXT NOT NULL,
        records_collected INTEGER NOT NULL,
        valid_records INTEGER NOT NULL,
        duplicate_records_removed INTEGER NOT NULL,
        missing_values_handled INTEGER NOT NULL,
        invalid_prices_filtered INTEGER NOT NULL,
        data_quality_pct REAL NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_key ON airfare_observations(route_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flight_date ON airfare_observations(flight_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_airline ON airfare_observations(airline_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_window ON airfare_observations(advance_window_tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON airfare_observations(data_source);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_demand ON airfare_observations(is_high_demand_period);")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized successfully.")
