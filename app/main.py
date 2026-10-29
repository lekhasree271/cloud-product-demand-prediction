"""
Cloud-Based Product Demand Prediction System Gateway
FastAPI Application serving ML Forecasting APIs, Inventory Analytics,
and the Cloud Supply Chain Management Dashboard.
"""

import io
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings, BASE_DIR
from app.ml.models import forecaster
from app.cloud.s3_storage import s3_storage
from app.cloud.dynamodb_store import dynamodb_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("DemandForecast.Gateway")

app = FastAPI(
    title="Cloud-Based Product Demand Prediction System",
    description="Enterprise Machine Learning & AWS Free-Tier Cloud Supply Chain Solution",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static UI
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Pydantic Schemas
class PredictRequest(BaseModel):
    product_id: str
    horizon_days: int = 14
    discount_percent: Optional[float] = None
    promotional_campaign: Optional[int] = None
    is_holiday: Optional[int] = None


class TrainRequest(BaseModel):
    model_type: str = "RandomForest"  # "RandomForest", "GradientBoosting", "LinearRegression"


# Global helper to get current active dataset
def get_current_df() -> pd.DataFrame:
    if not settings.DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail="Sales dataset not found.")
    df = pd.read_csv(settings.DATASET_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Cloud-Based Product Demand Prediction API is active."}


@app.get("/api/cloud/status")
async def get_cloud_status():
    """Returns AWS Free Tier cloud status and infrastructure metrics."""
    return {
        "cloud_provider": "AWS_FREE_TIER",
        "region": settings.AWS_REGION,
        "monthly_cloud_cost": "$0.00 (Free Tier)",
        "services": {
            "s3_storage": {
                "name": "Amazon S3",
                "bucket": settings.S3_BUCKET_NAME,
                "tier": "5 GB Standard Storage (Free Tier)",
                "status": "ONLINE"
            },
            "dynamodb_database": {
                "name": "Amazon DynamoDB",
                "table": settings.DYNAMODB_TABLE_NAME,
                "tier": "25 GB Storage & 25 RCU/WCU (Always Free)",
                "status": "ONLINE"
            },
            "compute_engine": {
                "name": "AWS Lambda / Elastic Beanstalk",
                "tier": "1,000,000 Free Requests/Month",
                "status": "READY"
            }
        },
        "model_engine": {
            "active_model": forecaster.model_type,
            "trained_at": forecaster.last_trained_at or "Auto-Trained",
            "metrics": forecaster.metrics
        }
    }


@app.get("/api/dataset/summary")
async def get_dataset_summary():
    """Returns catalog list, total sales, date ranges, and categories."""
    df = get_current_df()

    products = []
    for pid, group in df.groupby("product_id"):
        products.append({
            "product_id": pid,
            "product_name": group["product_name"].iloc[0],
            "category": group["category"].iloc[0],
            "unit_price": float(group["unit_price"].iloc[-1]),
            "current_inventory": int(group["current_inventory"].iloc[-1]),
            "total_units_sold": int(group["units_sold"].sum()),
            "avg_daily_sales": round(float(group["units_sold"].mean()), 1)
        })

    categories = df["category"].value_counts().to_dict()

    return {
        "total_records": len(df),
        "start_date": df["date"].min().strftime("%Y-%m-%d"),
        "end_date": df["date"].max().strftime("%Y-%m-%d"),
        "product_count": len(products),
        "products": products,
        "categories": categories,
        "active_model": forecaster.model_type,
        "model_metrics": forecaster.metrics
    }


@app.post("/api/dataset/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads a customized sales CSV dataset and uploads to S3."""
    content = await file.read()
    try:
        new_df = pd.read_csv(io.BytesIO(content))
        required_cols = {"date", "product_id", "product_name", "units_sold", "unit_price"}
        missing = required_cols - set(new_df.columns)
        if missing:
            raise HTTPException(status_code=400, detail=f"CSV missing required columns: {missing}")

        # Save to S3 (or local S3 store)
        s3_meta = s3_storage.upload_dataset(content, file.filename)

        # Overwrite active dataset path
        settings.DATASET_PATH.write_bytes(content)

        # Retrain model on new dataset
        train_result = forecaster.train(new_df, model_type="RandomForest")

        return {
            "status": "UPLOADED_AND_TRAINED",
            "filename": file.filename,
            "records": len(new_df),
            "s3_metadata": s3_meta,
            "model_metrics": train_result["metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dataset processing error: {e}")


@app.post("/api/model/train")
async def train_model_endpoint(req: TrainRequest):
    """Trains or switches the ML algorithm (RandomForest, GradientBoosting, LinearRegression)."""
    df = get_current_df()
    result = forecaster.train(df, model_type=req.model_type)
    return result


@app.post("/api/predict/demand")
async def predict_demand(req: PredictRequest):
    """Generates demand forecasts and inventory risk alerts."""
    df = get_current_df()
    try:
        forecast = forecaster.predict_future(
            df=df,
            product_id=req.product_id,
            horizon_days=req.horizon_days,
            discount_override=req.discount_percent,
            promo_override=req.promotional_campaign,
            holiday_override=req.is_holiday
        )

        # Save to DynamoDB
        rec_id = dynamodb_store.save_forecast(forecast)
        forecast["forecast_id"] = rec_id
        return forecast
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@app.get("/api/inventory/alerts")
async def get_inventory_alerts():
    """Returns active overstock and stockout warning alerts."""
    alerts = dynamodb_store.list_alerts()
    forecasts = dynamodb_store.list_recent_forecasts(limit=10)
    return {
        "total_alerts": len(alerts),
        "alerts": alerts,
        "recent_forecast_history": forecasts
    }
