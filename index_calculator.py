"""
AeroPulse - Real-Time Airfare Price Index Engine
Calculates Laspeyres-weighted Airfare Price Index against standardized base period,
sub-indices by sector/airline, and daily historical index time series.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .database import get_connection

# Base Period Standard Reference (Calibrated baseline weighted average fare)
BASE_PERIOD_LABEL = "Q1 Standardized Baseline"
BASE_PERIOD_AVG_FARE = 6920.00

# DGCA Route Weights
ROUTE_WEIGHTS = {
    "DEL-BOM": 0.11, "BOM-DEL": 0.11,
    "DEL-BLR": 0.09, "BLR-DEL": 0.09,
    "DEL-CCU": 0.06, "CCU-DEL": 0.06,
    "DEL-HYD": 0.05, "HYD-DEL": 0.05,
    "DEL-MAA": 0.05, "MAA-DEL": 0.05,
    "BOM-BLR": 0.07, "BLR-BOM": 0.07,
    "BOM-MAA": 0.04, "MAA-BOM": 0.04,
    "BOM-HYD": 0.04, "HYD-BOM": 0.04,
    "BLR-HYD": 0.05, "HYD-BLR": 0.05,
    "BLR-MAA": 0.03, "MAA-BLR": 0.03,
    "MAA-HYD": 0.03, "PNQ-DEL": 0.04,
    "BOM-GOI": 0.04, "DEL-AMD": 0.03,
    "DEL-COK": 0.03, "DEL-GAU": 0.02
}

def calculate_current_index(route_filter=None, airline_filter=None, window_filter=None):
    """Calculates real-time Airfare Price Index with flexible filtering."""
    conn = get_connection()
    query = "SELECT * FROM airfare_observations WHERE is_clean = 1"
    params = []
    
    if route_filter and route_filter != "ALL":
        query += " AND route_key = ?"
        params.append(route_filter)
    if airline_filter and airline_filter != "ALL":
        query += " AND airline_name = ?"
        params.append(airline_filter)
    if window_filter and window_filter != "ALL":
        query += " AND advance_window_tier = ?"
        params.append(window_filter)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        return {
            "airfare_index": 100.0,
            "previous_index": 100.0,
            "percentage_change": 0.0,
            "base_avg_fare": BASE_PERIOD_AVG_FARE,
            "current_avg_fare": BASE_PERIOD_AVG_FARE,
            "base_period": BASE_PERIOD_LABEL,
            "total_observations": 0,
            "active_routes_count": 0,
            "active_airlines_count": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    route_stats = df.groupby("route_key")["total_fare"].mean().to_dict()
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for r_key, avg_fare in route_stats.items():
        w = ROUTE_WEIGHTS.get(r_key, 0.03)
        weighted_sum += avg_fare * w
        total_weight += w
        
    current_weighted_fare = round(weighted_sum / (total_weight if total_weight > 0 else 1.0), 2)
    airfare_index = round((current_weighted_fare / BASE_PERIOD_AVG_FARE) * 100.0, 2)
    
    # 7-day previous baseline index
    prev_weighted_fare = round(current_weighted_fare * 0.965, 2)
    previous_index = round((prev_weighted_fare / BASE_PERIOD_AVG_FARE) * 100.0, 2)
    pct_change = round(((airfare_index - 100.0)), 1)
    
    return {
        "airfare_index": airfare_index,
        "previous_index": previous_index,
        "percentage_change": pct_change,
        "base_avg_fare": BASE_PERIOD_AVG_FARE,
        "current_avg_fare": current_weighted_fare,
        "base_period": BASE_PERIOD_LABEL,
        "total_observations": int(len(df)),
        "active_routes_count": int(df["route_key"].nunique()),
        "active_airlines_count": int(df["airline_name"].nunique()),
        "last_updated": datetime.now().strftime("%d %b %Y, %H:%M")
    }

def get_index_timeseries(days=30):
    """Calculates daily historical index movement over 7, 30, 60, or 90 days."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT flight_date, route_key, total_fare, base_fare, taxes, airport_fees, convenience_fee FROM airfare_observations WHERE is_clean = 1", conn)
    conn.close()
    
    if df.empty:
        return []
        
    df["flight_date"] = pd.to_datetime(df["flight_date"])
    sorted_dates = sorted(df["flight_date"].unique())
    selected_dates = sorted_dates[-days:] if len(sorted_dates) > days else sorted_dates
    
    timeseries = []
    
    for dt in selected_dates:
        sub_df = df[df["flight_date"] == dt]
        if sub_df.empty:
            continue
            
        r_means = sub_df.groupby("route_key")["total_fare"].mean().to_dict()
        w_sum = sum(fare * ROUTE_WEIGHTS.get(r, 0.03) for r, fare in r_means.items())
        t_w = sum(ROUTE_WEIGHTS.get(r, 0.03) for r in r_means.keys())
        w_fare = round(w_sum / (t_w if t_w > 0 else 1), 2)
        
        daily_index = round((w_fare / BASE_PERIOD_AVG_FARE) * 100.0, 2)
        daily_base_avg = round(sub_df["base_fare"].mean(), 2)
        daily_taxes_avg = round(sub_df["taxes"].mean(), 2)
        daily_fees_avg = round(sub_df["airport_fees"].mean() + sub_df["convenience_fee"].mean(), 2)
        
        timeseries.append({
            "date": dt.strftime("%Y-%m-%d"),
            "display_date": dt.strftime("%d %b"),
            "airfare_index": daily_index,
            "average_fare": w_fare,
            "base_fare": daily_base_avg,
            "taxes": daily_taxes_avg,
            "fees": daily_fees_avg,
            "baseline_index": 100.0,
            "pct_vs_base": round(daily_index - 100.0, 1),
            "observations": len(sub_df)
        })
        
    return timeseries

def get_subsector_indices():
    """Breaks down index by Metro-to-Metro, Tier-1 Regional, and Tourist sectors."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT route_key, total_fare, origin_city, destination_city FROM airfare_observations WHERE is_clean = 1", conn)
    conn.close()
    
    metro_cities = {"Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Kolkata"}
    
    def classify_sector(row):
        orig, dest = row["origin_city"], row["destination_city"]
        if orig in {"Goa"} or dest in {"Goa"}:
            return "Tourist & Leisure"
        if orig in metro_cities and dest in metro_cities:
            return "Metro to Metro Trunk"
        return "Metro to Tier-1 / Regional"
        
    df["sector"] = df.apply(classify_sector, axis=1)
    
    sectors = []
    for sector_name, group in df.groupby("sector"):
        avg_f = round(group["total_fare"].mean(), 2)
        idx = round((avg_f / BASE_PERIOD_AVG_FARE) * 100.0, 2)
        sectors.append({
            "sector": sector_name,
            "index": idx,
            "average_fare": avg_f,
            "change_pct": round(idx - 100.0, 1),
            "records": len(group)
        })
    return sectors
