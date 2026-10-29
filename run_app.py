"""
Product Demand Prediction Application Launcher
Initializes dataset, pre-trains Random Forest ML model,
and launches the FastAPI executive dashboard.
"""

import sys
import os
import uvicorn
import pandas as pd
from pathlib import Path

# Add project root to Python module search path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.config import settings
from app.ml.models import forecaster


def print_banner():
    banner = f"""
======================================================================
     CLOUD-BASED PRODUCT DEMAND PREDICTION SYSTEM (AWS FREE TIER)
     Machine Learning Supply Chain & Inventory Optimization
======================================================================
  * Cloud Environment    : {settings.CLOUD_PROVIDER} (Zero-Cost / No Subscription)
  * AWS Storage Service  : Amazon S3 (Historical Sales Datasets)
  * AWS Database Service : Amazon DynamoDB (Forecasts & Stockout Alerts)
  * Machine Learning     : Random Forest / Gradient Boosting / Ridge
  * Web Dashboard        : http://localhost:{settings.PORT}
  * Interactive API Docs : http://localhost:{settings.PORT}/docs
  * Cloud Status API     : http://localhost:{settings.PORT}/api/cloud/status
======================================================================
"""
    print(banner)


def initialize_app():
    """Ensures dataset exists and pre-trains ML model for immediate usage."""
    if not settings.DATASET_PATH.exists():
        print("[!] Generating sample retail sales dataset...")
        import subprocess
        gen_script = settings.DATA_DIR / "generate_data.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)

    # Pre-train ML model
    print("[*] Pre-training Random Forest demand forecasting model...")
    df = pd.read_csv(settings.DATASET_PATH)
    result = forecaster.train(df, model_type="RandomForest")
    metrics = result["metrics"]
    print(f"[✓] Model trained successfully! R² Score: {metrics['r2_score']} | MAE: ±{metrics['mae']} units")


if __name__ == "__main__":
    initialize_app()
    print_banner()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=False
    )
