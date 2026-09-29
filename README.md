# ✈️ AeroPulse — Real-Time Airfare Intelligence Platform

> **Tagline:** Real-Time Airfare Intelligence  
> **Subtitle:** Transforming Airfare Data into Actionable Insights

AeroPulse is a standalone professional aviation-data intelligence platform that automatically collects, cleans, normalizes, analyzes, and visualizes domestic airfare data across India, computing a high-frequency **Real-Time Airfare Price Index** with explainable statistical price spike anomaly detection.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/AeroPulse.git
cd AeroPulse
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python run.py
```

Open your browser at: **`http://127.0.0.1:8000`**

---

## 📁 Repository Structure

```text
├── run.py                       # Application entry point / server launcher
├── requirements.txt             # Python project dependencies
├── .gitignore                   # Git ignore configuration
│
├── backend/                     # Backend Python Modules (FastAPI & Analytics)
│   ├── main.py                  # API endpoints and static file routing
│   ├── database.py              # SQLite storage & database initialization
│   ├── data_generator.py        # Realistic multi-route dataset engine
│   ├── index_calculator.py      # Laspeyres Price Index mathematical engine
│   ├── spike_detector.py        # Z-score & IQR statistical price spike detector
│   └── quality_pipeline.py      # Ingestion audit and live stream simulator
│
├── static/                      # Frontend Application (Light Theme UI)
│   ├── index.html               # Single-page application markup & views
│   ├── styles.css               # Professional Light Theme styles
│   ├── app.js                   # Application state, UI routing & interactions
│   └── charts.js                # Canvas charting engine
│
└── data/
    └── aeropulse.db             # Seeded SQLite database
```

---

## 📊 Key Features
- **Real-Time Airfare Price Index:** Laspeyres weighted formulation comparing current fares against base benchmark.
- **Explainable Price Spike Detection:** Identifies statistical outliers ($Z \ge 1.95$) with root-cause diagnostic drivers.
- **India Flight Corridor Heatmap:** Interactive network across 12 major Indian airport hubs with route drilldown.
- **Airline & Source Fare Breakdown:** Detailed unbundling into Base Fare, GST, UDF, and Convenience Fees.
- **Advance Booking Velocity ($T+N$):** Tracks dynamic pricing curves from $T+45$ to $T+1$.
- **Data Quality & Simulation:** Live data quality audit and real-time batch stream simulation.
