"""
Configuration Management for Cloud-Based Product Demand Prediction System
Designed for AWS Free Tier compliance with zero-login offline simulation fallback.
"""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class SystemSettings(BaseModel):
    # Cloud Deployment Mode: "AWS_FREE_TIER" or "LOCAL_SIMULATION"
    CLOUD_PROVIDER: str = os.getenv("CLOUD_PROVIDER", "AWS_FREE_TIER").upper()

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    DATASET_PATH: Path = BASE_DIR / "data" / "sample_sales_data.csv"
    MODELS_DIR: Path = BASE_DIR / "data" / "trained_models"
    S3_LOCAL_STORAGE: Path = BASE_DIR / "data" / "s3_bucket"
    SQLITE_PATH: Path = BASE_DIR / "data" / "forecasts_store.db"

    # Machine Learning Defaults
    DEFAULT_MODEL_TYPE: str = "RandomForest"  # "RandomForest", "GradientBoosting", "LinearRegression"
    TEST_SPLIT_RATIO: float = 0.20
    CV_FOLDS: int = 5
    N_ESTIMATORS: int = 100
    RANDOM_STATE: int = 42

    # AWS Free Tier Cloud Services (5GB S3, 25GB DynamoDB Free Tier)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "demand-forecasting-sales-data")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "ProductDemandForecasts")
    LOCALSTACK_ENDPOINT: str = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")

    # Inventory Constants (Service Level 95% -> Z = 1.65, Lead time = 7 days)
    SERVICE_LEVEL_Z: float = 1.65
    DEFAULT_LEAD_TIME_DAYS: int = 7
    ORDERING_COST_PER_ORDER: float = 50.0  # $ per purchase order (S)
    HOLDING_COST_RATE: float = 0.20        # 20% of unit price annually (H)

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = SystemSettings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.S3_LOCAL_STORAGE.mkdir(parents=True, exist_ok=True)
