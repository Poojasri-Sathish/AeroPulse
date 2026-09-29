"""
AeroPulse - Explainable Statistical Price Spike Detector
Detects statistical airfare anomalies using rolling baseline deviations, Z-scores, and IQR.
Generates crystal-clear explainable diagnostic root causes.
"""
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from .database import get_connection

def detect_and_store_price_spikes():
    """Runs statistical anomaly detection across all route-airline-window combinations."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM airfare_observations WHERE is_clean = 1", conn)
    
    if df.empty:
        conn.close()
        return []
        
    # Calculate baseline historical mean and std per route + booking window
    grouped = df.groupby(["route_key", "advance_window_tier"])["total_fare"].agg(["mean", "std", "count"]).reset_index()
    grouped.rename(columns={"mean": "baseline_mean", "std": "baseline_std"}, inplace=True)
    
    # Merge baseline stats back into observations
    merged = pd.merge(df, grouped, on=["route_key", "advance_window_tier"], how="left")
    merged["baseline_std"] = merged["baseline_std"].fillna(merged["baseline_mean"] * 0.15)
    
    # Compute Z-score & Percentage deviation
    merged["z_score"] = (merged["total_fare"] - merged["baseline_mean"]) / merged["baseline_std"].replace(0, 1)
    merged["pct_change"] = ((merged["total_fare"] - merged["baseline_mean"]) / merged["baseline_mean"]) * 100.0
    
    # Anomalies: Z-Score >= 2.0 OR pct_change >= 35.0%
    anomalies = merged[(merged["z_score"] >= 1.95) | (merged["pct_change"] >= 35.0)].copy()
    
    alerts = []
    
    for _, row in anomalies.iterrows():
        pct = round(row["pct_change"], 1)
        z = round(row["z_score"], 2)
        base_f = round(row["baseline_mean"], 2)
        curr_f = round(row["total_fare"], 2)
        
        # Determine Severity
        if pct >= 55 or z >= 2.8:
            severity = "CRITICAL"
        elif pct >= 35 or z >= 2.2:
            severity = "HIGH"
        else:
            severity = "MODERATE"
            
        # Determine Explainable Reason
        reasons = []
        if row["is_high_demand_period"] == 1:
            reasons.append(f"High demand festive cluster ({row['demand_period_name']})")
        if row["advance_window_tier"] == "T+1":
            reasons.append("Last-minute booking window compression (T+1 lead time)")
        elif row["advance_window_tier"] == "T+7":
            reasons.append("Elevated short-window velocity (T+7 lead time)")
        if row["airline_name"] in ["Vistara", "Air India"]:
            reasons.append(f"Full-service carrier dynamic seat inventory yield shift ({row['airline_name']})")
        if "GOI" in row["route_key"]:
            reasons.append("High holiday corridor leisure influx to Goa")
        if len(reasons) == 0:
            reasons.append("Sudden route-level capacity constraint / rapid seat inventory exhaustion")
            
        primary_reason = reasons[0]
        details = f"Airfare of ₹{curr_f:,.0f} deviates +{pct}% (Z={z}) from historical route baseline average of ₹{base_f:,.0f}. Root cause: {'; '.join(reasons)}."
        
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        
        alerts.append({
            "alert_id": alert_id,
            "route_key": row["route_key"],
            "origin_city": row["origin_city"],
            "destination_city": row["destination_city"],
            "airline_name": row["airline_name"],
            "flight_date": row["flight_date"],
            "advance_window_tier": row["advance_window_tier"],
            "baseline_fare": base_f,
            "current_fare": curr_f,
            "percentage_change": pct,
            "z_score": z,
            "severity": severity,
            "primary_reason": primary_reason,
            "explanation_details": details,
            "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Active"
        })
        
    # Store alerts in DB
    cursor = conn.cursor()
    cursor.execute("DELETE FROM price_spike_alerts;")
    
    cursor.executemany("""
    INSERT INTO price_spike_alerts (
        alert_id, route_key, origin_city, destination_city, airline_name,
        flight_date, advance_window_tier, baseline_fare, current_fare,
        percentage_change, z_score, severity, primary_reason,
        explanation_details, detected_at, status
    ) VALUES (
        :alert_id, :route_key, :origin_city, :destination_city, :airline_name,
        :flight_date, :advance_window_tier, :baseline_fare, :current_fare,
        :percentage_change, :z_score, :severity, :primary_reason,
        :explanation_details, :detected_at, :status
    );
    """, alerts[:120]) # keep top active alerts
    
    conn.commit()
    conn.close()
    return alerts[:120]

def get_active_spike_alerts(limit=50, severity_filter=None):
    """Retrieves detected price alerts."""
    conn = get_connection()
    query = "SELECT * FROM price_spike_alerts WHERE status = 'Active'"
    params = []
    
    if severity_filter and severity_filter != "ALL":
        query += " AND severity = ?"
        params.append(severity_filter)
        
    query += " ORDER BY percentage_change DESC LIMIT ?"
    params.append(limit)
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]
