"""
AeroPulse - Standalone Professional Airfare Intelligence Platform
FastAPI Backend Engine
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import pandas as pd
import io
from datetime import datetime

from .database import init_db, get_connection
from .data_generator import generate_demo_dataset, AIRPORTS, ROUTES_CONFIG, AIRLINES, DATA_SOURCES, BOOKING_WINDOWS, DEMAND_PERIODS
from .index_calculator import calculate_current_index, get_index_timeseries, get_subsector_indices, BASE_PERIOD_LABEL, BASE_PERIOD_AVG_FARE
from .spike_detector import detect_and_store_price_spikes, get_active_spike_alerts
from .quality_pipeline import get_quality_metrics, simulate_realtime_ingestion_batch

app = FastAPI(
    title="AeroPulse API",
    description="Real-Time Airfare Intelligence Platform API",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"

@app.on_event("startup")
def on_startup():
    """Ensure database is initialized and populated with realistic 90-day dataset."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM airfare_observations;")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count < 5000:
        print("Populating AeroPulse with 11,000+ realistic domestic airfare records...")
        generate_demo_dataset(11000)
        detect_and_store_price_spikes()
        print("AeroPulse database populated and price spike anomalies detected.")
    else:
        print(f"AeroPulse database ready with {count} observations.")

# ====================================================================
# API ENDPOINTS
# ====================================================================

@app.get("/api/kpis")
def get_dashboard_kpis(
    route: str = Query("ALL"),
    airline: str = Query("ALL"),
    window: str = Query("ALL")
):
    """Retrieve top-level KPI metrics including real-time Airfare Index."""
    index_data = calculate_current_index(route, airline, window)
    alerts = get_active_spike_alerts(limit=6)
    quality = get_quality_metrics()
    
    return {
        "kpis": index_data,
        "active_alerts_count": len(get_active_spike_alerts(limit=100)),
        "recent_alerts": alerts,
        "data_quality": quality
    }

@app.get("/api/index-trend")
def get_index_trend(days: int = Query(30)):
    """Retrieve historical index and fare breakdown timeseries (7D, 30D, 60D, 90D)."""
    return {
        "timeseries": get_index_timeseries(days),
        "base_period_label": BASE_PERIOD_LABEL,
        "base_avg_fare": BASE_PERIOD_AVG_FARE
    }

@app.get("/api/subsectors")
def get_subsectors():
    """Retrieve sectoral index decomposition."""
    return {
        "subsectors": get_subsector_indices()
    }

@app.get("/api/top-routes")
def get_top_routes(limit: int = Query(8)):
    """Retrieve top 6-8 domestic routes for immediate dashboard preview."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT route_key, origin_city, destination_city, total_fare FROM airfare_observations WHERE is_clean = 1", conn)
    conn.close()
    
    if df.empty:
        return {"routes": []}
        
    grouped = df.groupby(["route_key", "origin_city", "destination_city"]).agg(
        avg_fare=("total_fare", "mean"),
        count=("total_fare", "count")
    ).reset_index()
    
    top_routes = []
    for _, row in grouped.iterrows():
        avg_f = round(row["avg_fare"], 2)
        r_index = round((avg_f / BASE_PERIOD_AVG_FARE) * 100.0, 1)
        pct_change = round(r_index - 100.0, 1)
        
        top_routes.append({
            "route_key": row["route_key"],
            "origin_city": row["origin_city"],
            "destination_city": row["destination_city"],
            "route_label": f"{row['origin_city']} → {row['destination_city']}",
            "avg_fare": avg_f,
            "airfare_index": r_index,
            "percentage_change": pct_change,
            "trend": "up" if pct_change >= 0 else "down",
            "observations": int(row["count"])
        })
        
    top_routes.sort(key=lambda x: x["observations"], reverse=True)
    return {"top_routes": top_routes[:limit]}

@app.get("/api/routes")
def get_route_analytics():
    """Retrieve route matrix with coordinates for India network map."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT route_key, origin_code, origin_city, destination_code, destination_city, total_fare, airline_name FROM airfare_observations WHERE is_clean = 1", conn)
    conn.close()
    
    if df.empty:
        return {"routes": [], "airports": AIRPORTS}
        
    grouped = df.groupby(["route_key", "origin_code", "origin_city", "destination_code", "destination_city"]).agg(
        avg_fare=("total_fare", "mean"),
        min_fare=("total_fare", "min"),
        max_fare=("total_fare", "max"),
        obs_count=("total_fare", "count"),
        airlines=("airline_name", "nunique")
    ).reset_index()
    
    routes_list = []
    for _, row in grouped.iterrows():
        avg_f = round(row["avg_fare"], 2)
        r_index = round((avg_f / BASE_PERIOD_AVG_FARE) * 100.0, 1)
        
        orig_meta = AIRPORTS.get(row["origin_code"], {"lat": 20.0, "lng": 77.0})
        dest_meta = AIRPORTS.get(row["destination_code"], {"lat": 20.0, "lng": 77.0})
        
        if avg_f > 6300:
            tier = "High"
            badge_color = "red"
        elif avg_f > 4600:
            tier = "Medium"
            badge_color = "orange"
        else:
            tier = "Low"
            badge_color = "green"
            
        routes_list.append({
            "route_key": row["route_key"],
            "origin_code": row["origin_code"],
            "origin_city": row["origin_city"],
            "destination_code": row["destination_code"],
            "destination_city": row["destination_city"],
            "avg_fare": avg_f,
            "min_fare": round(row["min_fare"], 2),
            "max_fare": round(row["max_fare"], 2),
            "airfare_index": r_index,
            "tier": tier,
            "badge_color": badge_color,
            "airlines_count": int(row["airlines"]),
            "observations_count": int(row["obs_count"]),
            "origin_lat": orig_meta["lat"],
            "origin_lng": orig_meta["lng"],
            "dest_lat": dest_meta["lat"],
            "dest_lng": dest_meta["lng"]
        })
        
    routes_list.sort(key=lambda x: x["avg_fare"], reverse=True)
    return {"routes": routes_list, "airports": AIRPORTS}

@app.get("/api/route-drilldown/{route_key}")
def get_route_drilldown(route_key: str):
    """Retrieve granular analytics, airline share, and booking curve for a specific route."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM airfare_observations WHERE route_key = ? AND is_clean = 1", conn, params=[route_key])
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Route not found")
        
    avg_f = round(df["total_fare"].mean(), 2)
    r_index = round((avg_f / BASE_PERIOD_AVG_FARE) * 100.0, 1)
    
    airline_breakdown = []
    for a_name, grp in df.groupby("airline_name"):
        airline_breakdown.append({
            "airline": a_name,
            "avg_fare": round(grp["total_fare"].mean(), 2),
            "min_fare": round(grp["total_fare"].min(), 2),
            "observations": len(grp)
        })
    airline_breakdown.sort(key=lambda x: x["avg_fare"])
    
    window_order = ["T+45", "T+30", "T+15", "T+7", "T+1"]
    window_curve = []
    for w in window_order:
        w_df = df[df["advance_window_tier"] == w]
        if not w_df.empty:
            window_curve.append({
                "window": w,
                "avg_fare": round(w_df["total_fare"].mean(), 2),
                "base_fare": round(w_df["base_fare"].mean(), 2)
            })
            
    samples = df.sort_values(by="collection_timestamp", ascending=False).head(10).to_dict(orient="records")
    
    return {
        "route_key": route_key,
        "origin_city": df.iloc[0]["origin_city"],
        "destination_city": df.iloc[0]["destination_city"],
        "average_fare": avg_f,
        "airfare_index": r_index,
        "airline_breakdown": airline_breakdown,
        "window_curve": window_curve,
        "recent_observations": samples
    }

@app.get("/api/airline-comparison")
def get_airline_comparison(route_key: str = Query("ALL")):
    """Compare fares, fare components (base, taxes, fees) across all 6 airlines."""
    conn = get_connection()
    if route_key == "ALL":
        df = pd.read_sql_query("SELECT * FROM airfare_observations WHERE is_clean = 1", conn)
        origin_city = "All India Network"
        dest_city = "All Corridors"
    else:
        df = pd.read_sql_query("SELECT * FROM airfare_observations WHERE route_key = ? AND is_clean = 1", conn, params=[route_key])
        if df.empty:
            df = pd.read_sql_query("SELECT * FROM airfare_observations WHERE route_key = 'MAA-DEL' AND is_clean = 1", conn)
            route_key = "MAA-DEL"
        origin_city = df.iloc[0]["origin_city"]
        dest_city = df.iloc[0]["destination_city"]
    conn.close()
    
    airline_stats = []
    for a_name, grp in df.groupby("airline_name"):
        avg_f = round(grp["total_fare"].mean(), 2)
        idx = round((avg_f / BASE_PERIOD_AVG_FARE) * 100.0, 1)
        airline_stats.append({
            "airline": a_name,
            "avg_fare": avg_f,
            "airfare_index": idx,
            "base_fare": round(grp["base_fare"].mean(), 2),
            "taxes": round(grp["taxes"].mean(), 2),
            "airport_fees": round(grp["airport_fees"].mean(), 2),
            "convenience_fee": round(grp["convenience_fee"].mean(), 2),
            "min_fare": round(grp["total_fare"].min(), 2),
            "max_fare": round(grp["total_fare"].max(), 2),
            "routes_count": int(grp["route_key"].nunique()),
            "observations": len(grp)
        })
    airline_stats.sort(key=lambda x: x["avg_fare"])
    
    source_stats = []
    for s_name, grp in df.groupby("data_source"):
        source_stats.append({
            "source": s_name,
            "avg_fare": round(grp["total_fare"].mean(), 2),
            "avg_convenience_fee": round(grp["convenience_fee"].mean(), 2),
            "observations": len(grp)
        })
    source_stats.sort(key=lambda x: x["avg_fare"])
    
    return {
        "route_key": route_key,
        "origin_city": origin_city,
        "destination_city": dest_city,
        "overall_route_avg": round(df["total_fare"].mean(), 2),
        "airlines": airline_stats,
        "sources": source_stats,
        "all_available_routes": ["ALL"] + [r[0] for r in ROUTES_CONFIG]
    }

@app.get("/api/price-spikes")
def get_price_spikes(severity: str = Query("ALL")):
    """Retrieve explainable statistical price spike alerts."""
    alerts = get_active_spike_alerts(limit=80, severity_filter=severity)
    return {
        "alerts": alerts,
        "total_active": len(alerts),
        "methodology": "Explainable rolling Z-score anomaly detector (threshold Z >= 1.95 or deviation >= +35% vs baseline route-window mean)."
    }

@app.get("/api/booking-window")
def get_booking_window_analysis(route_key: str = Query("ALL")):
    """Analyze airfare escalation across T+1, T+7, T+15, T+30, T+45 booking windows."""
    conn = get_connection()
    query = "SELECT advance_window_tier, advance_window_days, base_fare, total_fare FROM airfare_observations WHERE is_clean = 1"
    params = []
    if route_key != "ALL":
        query += " AND route_key = ?"
        params.append(route_key)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    order = ["T+45", "T+30", "T+15", "T+7", "T+1"]
    results = []
    
    t45_avg = df[df["advance_window_tier"] == "T+45"]["total_fare"].mean() if not df[df["advance_window_tier"] == "T+45"].empty else 4500
    t30_avg = df[df["advance_window_tier"] == "T+30"]["total_fare"].mean() if not df[df["advance_window_tier"] == "T+30"].empty else 5000
    t1_avg = df[df["advance_window_tier"] == "T+1"]["total_fare"].mean() if not df[df["advance_window_tier"] == "T+1"].empty else 8500
    
    for tier in order:
        sub = df[df["advance_window_tier"] == tier]
        if not sub.empty:
            avg_tot = round(sub["total_fare"].mean(), 2)
            avg_base = round(sub["base_fare"].mean(), 2)
            esc_pct = round(((avg_tot - t45_avg) / t45_avg) * 100.0, 1)
            days = sub.iloc[0]["advance_window_days"]
            
            results.append({
                "tier": tier,
                "days_in_advance": int(days),
                "avg_total_fare": avg_tot,
                "avg_base_fare": avg_base,
                "escalation_vs_t45_pct": esc_pct,
                "observations": len(sub)
            })
            
    t1_vs_t30_pct = round(((t1_avg - t30_avg) / t30_avg) * 100.0, 1)
    insight = f"T+1 last-minute departure fares average {t1_vs_t30_pct}% higher than T+30 advance bookings ({len(df):,} verified observations)."
    
    return {
        "booking_windows": results,
        "key_insight": insight,
        "t1_vs_t30_pct": t1_vs_t30_pct,
        "available_routes": ["ALL"] + [r[0] for r in ROUTES_CONFIG]
    }

@app.get("/api/festival-demand")
def get_festival_demand_analysis():
    """Compare festive and peak demand periods against standard baseline."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT is_high_demand_period, demand_period_name, total_fare, route_key FROM airfare_observations WHERE is_clean = 1", conn)
    conn.close()
    
    baseline_fare = round(df[df["is_high_demand_period"] == 0]["total_fare"].mean(), 2)
    
    festivals = []
    for p_name, grp in df[df["is_high_demand_period"] == 1].groupby("demand_period_name"):
        p_avg = round(grp["total_fare"].mean(), 2)
        diff_pct = round(((p_avg - baseline_fare) / baseline_fare) * 100.0, 1)
        festivals.append({
            "period_name": p_name,
            "period_avg_fare": p_avg,
            "baseline_fare": baseline_fare,
            "percentage_difference": diff_pct,
            "surge_multiplier": round(p_avg / baseline_fare, 2),
            "observations": len(grp)
        })
        
    festivals.sort(key=lambda x: x["percentage_difference"], reverse=True)
    return {
        "baseline_average_fare": baseline_fare,
        "demand_periods": festivals
    }

@app.get("/api/data-explorer")
def get_data_explorer_records(
    search: str = Query(""),
    origin: str = Query("ALL"),
    destination: str = Query("ALL"),
    airline: str = Query("ALL"),
    window: str = Query("ALL"),
    source: str = Query("ALL"),
    page: int = Query(1),
    limit: int = Query(25)
):
    """Searchable, filterable, and paginated raw & cleaned airfare observations."""
    conn = get_connection()
    query = "SELECT * FROM airfare_observations WHERE 1=1"
    params = []
    
    if search:
        query += " AND (observation_id LIKE ? OR flight_number LIKE ? OR origin_city LIKE ? OR destination_city LIKE ?)"
        s_term = f"%{search}%"
        params.extend([s_term, s_term, s_term, s_term])
    if origin != "ALL":
        query += " AND origin_code = ?"
        params.append(origin)
    if destination != "ALL":
        query += " AND destination_code = ?"
        params.append(destination)
    if airline != "ALL":
        query += " AND airline_name = ?"
        params.append(airline)
    if window != "ALL":
        query += " AND advance_window_tier = ?"
        params.append(window)
    if source != "ALL":
        query += " AND data_source = ?"
        params.append(source)
        
    count_query = f"SELECT COUNT(*) FROM ({query})"
    cursor = conn.cursor()
    cursor.execute(count_query, params)
    total_matching = cursor.fetchone()[0]
    
    query += " ORDER BY flight_date DESC, id DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * limit
    params.extend([limit, offset])
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return {
        "records": df.to_dict(orient="records"),
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_matching,
            "total_pages": (total_matching + limit - 1) // limit
        },
        "filters": {
            "origins": list(AIRPORTS.keys()),
            "destinations": list(AIRPORTS.keys()),
            "airlines": [a["name"] for a in AIRLINES],
            "windows": [w["tier"] for w in BOOKING_WINDOWS],
            "sources": [s["name"] for s in DATA_SOURCES]
        }
    }

@app.get("/api/data-quality")
def get_pipeline_quality():
    """Retrieve data quality metrics, deduplication audit, and pipeline hygiene."""
    return get_quality_metrics()

@app.post("/api/simulate-ingestion")
def simulate_ingestion():
    """Simulate a fresh batch of ethical data scraping, normalization, and index update."""
    result = simulate_realtime_ingestion_batch(50)
    detect_and_store_price_spikes()
    return result

@app.get("/api/export-csv")
def export_csv(limit: int = Query(5000)):
    """Export cleaned airfare observations as CSV."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT observation_id, origin_city, destination_city, route_key, airline_name, flight_number, flight_date, advance_window_tier, base_fare, taxes, airport_fees, convenience_fee, total_fare, data_source FROM airfare_observations WHERE is_clean = 1 LIMIT ?", conn, params=[limit])
    conn.close()
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=aeropulse_airfare_intelligence_export.csv"
    return response

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "AeroPulse API running."}
