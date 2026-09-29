"""
AeroPulse - High-Fidelity Airfare Demo Data Engine
Generates 10,000+ authentic, varied domestic airfare observations across India
over a 90-day time horizon with realistic booking curves, fee unbundling, and surge anomalies.
"""
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .database import get_connection

AIRPORTS = {
    "DEL": {"city": "Delhi", "name": "Indira Gandhi International Airport", "tier": "Metro", "lat": 28.5562, "lng": 77.1000},
    "BOM": {"city": "Mumbai", "name": "Chhatrapati Shivaji Maharaj International", "tier": "Metro", "lat": 19.0896, "lng": 72.8656},
    "BLR": {"city": "Bengaluru", "name": "Kempegowda International Airport", "tier": "Metro", "lat": 13.1986, "lng": 77.7066},
    "MAA": {"city": "Chennai", "name": "Chennai International Airport", "tier": "Metro", "lat": 12.9941, "lng": 80.1709},
    "HYD": {"city": "Hyderabad", "name": "Rajiv Gandhi International Airport", "tier": "Metro", "lat": 17.2403, "lng": 78.4294},
    "CCU": {"city": "Kolkata", "name": "Netaji Subhash Chandra Bose International", "tier": "Metro", "lat": 22.6547, "lng": 88.4467},
    "PNQ": {"city": "Pune", "name": "Pune Airport", "tier": "Tier 1", "lat": 18.5822, "lng": 73.9197},
    "AMD": {"city": "Ahmedabad", "name": "Sardar Vallabhbhai Patel International", "tier": "Tier 1", "lat": 23.0772, "lng": 72.6347},
    "GOI": {"city": "Goa", "name": "Dabolim / Manohar International Airport", "tier": "Tourist", "lat": 15.3808, "lng": 73.8314},
    "COK": {"city": "Kochi", "name": "Cochin International Airport", "tier": "Tier 1", "lat": 10.1556, "lng": 76.3912},
    "GAU": {"city": "Guwahati", "name": "Lokpriya Gopinath Bordoloi International", "tier": "Tier 2", "lat": 26.1061, "lng": 91.5859},
    "JAI": {"city": "Jaipur", "name": "Jaipur International Airport", "tier": "Tier 1", "lat": 26.8242, "lng": 75.8122}
}

ROUTES_CONFIG = [
    # route_key, origin, destination, base_fare_range, traffic_weight
    ("DEL-BOM", "DEL", "BOM", (4350, 5850), 0.11),
    ("BOM-DEL", "BOM", "DEL", (4350, 5850), 0.11),
    ("DEL-BLR", "DEL", "BLR", (4950, 6450), 0.09),
    ("BLR-DEL", "BLR", "DEL", (4950, 6450), 0.09),
    ("DEL-CCU", "DEL", "CCU", (4650, 6150), 0.06),
    ("CCU-DEL", "CCU", "DEL", (4650, 6150), 0.06),
    ("DEL-HYD", "DEL", "HYD", (4450, 5950), 0.05),
    ("HYD-DEL", "HYD", "DEL", (4450, 5950), 0.05),
    ("DEL-MAA", "DEL", "MAA", (4750, 6250), 0.05),
    ("MAA-DEL", "MAA", "DEL", (4750, 6250), 0.05),
    ("BOM-BLR", "BOM", "BLR", (3750, 4950), 0.07),
    ("BLR-BOM", "BLR", "BOM", (3750, 4950), 0.07),
    ("BOM-MAA", "BOM", "MAA", (4050, 5350), 0.04),
    ("MAA-BOM", "MAA", "BOM", (4050, 5350), 0.04),
    ("BOM-HYD", "BOM", "HYD", (3450, 4650), 0.04),
    ("HYD-BOM", "HYD", "BOM", (3450, 4650), 0.04),
    ("BLR-HYD", "BLR", "HYD", (2850, 3950), 0.05),
    ("HYD-BLR", "HYD", "BLR", (2850, 3950), 0.05),
    ("BLR-MAA", "BLR", "MAA", (2350, 3350), 0.03),
    ("MAA-BLR", "MAA", "BLR", (2350, 3350), 0.03),
    ("MAA-HYD", "MAA", "HYD", (3150, 4250), 0.03),
    ("PNQ-DEL", "PNQ", "DEL", (4250, 5650), 0.04),
    ("BOM-GOI", "BOM", "GOI", (2950, 4350), 0.04),
    ("DEL-AMD", "DEL", "AMD", (3450, 4650), 0.03),
    ("DEL-COK", "DEL", "COK", (5550, 7350), 0.03),
    ("DEL-GAU", "DEL", "GAU", (5350, 7150), 0.02)
]

AIRLINES = [
    {"code": "6E", "name": "IndiGo", "market_share": 0.56, "multiplier": 0.96},
    {"code": "AI", "name": "Air India", "market_share": 0.16, "multiplier": 1.05},
    {"code": "IX", "name": "Air India Express", "market_share": 0.07, "multiplier": 0.94},
    {"code": "QP", "name": "Akasa Air", "market_share": 0.07, "multiplier": 0.93},
    {"code": "SG", "name": "SpiceJet", "market_share": 0.05, "multiplier": 0.92},
    {"code": "UK", "name": "Vistara", "market_share": 0.09, "multiplier": 1.10}
]

DATA_SOURCES = [
    {"name": "Airline Website", "fee_adj": 0},
    {"name": "MakeMyTrip", "fee_adj": 150},
    {"name": "EaseMyTrip", "fee_adj": 50},
    {"name": "Cleartrip", "fee_adj": 120},
    {"name": "Yatra", "fee_adj": 100}
]

BOOKING_WINDOWS = [
    {"tier": "T+1", "days": 1, "multiplier": 1.58, "volatility": 0.18},
    {"tier": "T+7", "days": 7, "multiplier": 1.28, "volatility": 0.12},
    {"tier": "T+15", "days": 15, "multiplier": 1.08, "volatility": 0.08},
    {"tier": "T+30", "days": 30, "multiplier": 0.98, "volatility": 0.05},
    {"tier": "T+45", "days": 45, "multiplier": 0.90, "volatility": 0.04}
]

DEMAND_PERIODS = [
    {"name": "Diwali Festive Rush", "dates": [("2026-10-25", "2026-11-05")], "multiplier": 1.48},
    {"name": "Pongal / Makar Sankranti", "dates": [("2026-01-12", "2026-01-18")], "multiplier": 1.42},
    {"name": "Christmas & New Year Surge", "dates": [("2026-12-20", "2027-01-05")], "multiplier": 1.52},
    {"name": "Independence Day Weekend", "dates": [("2026-08-13", "2026-08-18")], "multiplier": 1.34},
    {"name": "Durga Puja & Dussehra", "dates": [("2026-10-08", "2026-10-14")], "multiplier": 1.38}
]

def is_demand_period(date_str):
    for dp in DEMAND_PERIODS:
        for start, end in dp["dates"]:
            if start <= date_str <= end:
                return True, dp["name"], dp["multiplier"]
    return False, "Standard Baseline", 1.0

def generate_demo_dataset(num_records=11000):
    """Generates authentic varied domestic airfare observations across a 90-day time horizon."""
    records = []
    base_date = datetime.now()
    
    print(f"Generating {num_records} realistic domestic airfare observations spanning 90 days...")
    
    for i in range(num_records):
        r_choice = random.choices(ROUTES_CONFIG, weights=[r[4] for r in ROUTES_CONFIG])[0]
        route_key, orig_code, dest_code, base_range, _ = r_choice
        
        orig_info = AIRPORTS[orig_code]
        dest_info = AIRPORTS[dest_code]
        
        airline = random.choices(AIRLINES, weights=[a["market_share"] for a in AIRLINES])[0]
        b_win = random.choice(BOOKING_WINDOWS)
        
        # Spread dates over past 60 days to next 30 days (total 90 days coverage)
        day_offset = random.randint(-60, 30)
        flight_dt = base_date + timedelta(days=day_offset + b_win["days"])
        flight_date_str = flight_dt.strftime("%Y-%m-%d")
        
        collection_dt = flight_dt - timedelta(days=b_win["days"])
        collection_str = collection_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        is_surge, surge_name, surge_mult = is_demand_period(flight_date_str)
        weekday = flight_dt.weekday()
        weekend_mult = 1.12 if weekday in [4, 6] else 1.0
        
        raw_base = random.uniform(base_range[0], base_range[1])
        fare_class = "Economy Standard" if random.random() > 0.15 else "Economy Flex"
        class_mult = 1.25 if fare_class == "Economy Flex" else 1.0
        
        volatility = random.gauss(1.0, b_win["volatility"])
        
        # Inject controlled statistical price anomalies (~3.2% probability)
        is_spike_anomaly = random.random() < 0.032
        spike_mult = random.uniform(1.42, 1.82) if is_spike_anomaly else 1.0
        
        calculated_base = raw_base * airline["multiplier"] * b_win["multiplier"] * surge_mult * weekend_mult * class_mult * volatility * spike_mult
        calculated_base = max(1950.0, round(calculated_base, 2))
        
        # Realistic fee breakdown: Base + GST (5%) + Airport UDF/ADF (₹480 - ₹980) + Convenience Fee (₹299 - ₹450)
        taxes = round(calculated_base * 0.05, 2)
        airport_fees = round(random.uniform(480, 950), 2)
        source = random.choice(DATA_SOURCES)
        convenience_fee = round(random.uniform(299, 449) + source["fee_adj"], 2)
        total_fare = round(calculated_base + taxes + airport_fees + convenience_fee, 2)
        
        flight_num = f"{airline['code']}-{random.randint(101, 999)}"
        obs_id = f"AP-{uuid.uuid4().hex[:10].upper()}"
        
        records.append((
            obs_id, orig_code, orig_info["city"], dest_code, dest_info["city"],
            route_key, airline["code"], airline["name"], flight_num,
            flight_date_str, collection_str, b_win["days"], b_win["tier"],
            fare_class, calculated_base, taxes, airport_fees, convenience_fee,
            total_fare, source["name"], 1, "CLEAN_VALIDATED",
            1 if is_surge else 0, surge_name
        ))

    # Add duplicate & outlier noise to demonstrate data quality cleaning
    dirty_count = int(num_records * 0.015)
    for _ in range(dirty_count):
        sample = list(random.choice(records))
        sample[0] = f"AP-{uuid.uuid4().hex[:10].upper()}"
        sample[20] = 0
        sample[21] = "DUPLICATE_SOURCE_RECORD"
        records.append(tuple(sample))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM airfare_observations;")
    
    cursor.executemany("""
    INSERT INTO airfare_observations (
        observation_id, origin_code, origin_city, destination_code, destination_city,
        route_key, airline_code, airline_name, flight_number,
        flight_date, collection_timestamp, advance_window_days, advance_window_tier,
        fare_class, base_fare, taxes, airport_fees, convenience_fee,
        total_fare, data_source, is_clean, quality_flags,
        is_high_demand_period, demand_period_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)
    
    conn.commit()
    conn.close()
    print(f"Successfully generated and stored {len(records)} realistic airfare observations in SQLite.")

if __name__ == "__main__":
    from .database import init_db
    init_db()
    generate_demo_dataset(11000)
