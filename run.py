import uvicorn
import os
import sys
from pathlib import Path

# Ensure package path is recognized
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    print("=" * 65)
    print("  AeroPulse - Real-Time Airfare Intelligence Platform")
    print("  Tagline: Real-Time Airfare Intelligence")
    print("  Subtitle: Transforming Airfare Data into Actionable Insights")
    print("=" * 65)
    print("Starting AeroPulse server on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
