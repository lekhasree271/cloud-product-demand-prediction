"""
Feature Engineering Engine for Time-Series Demand Forecasting
Generates lag features, rolling moving averages, seasonality indicators,
and pricing elasticity variables with product baseline embeddings.
"""

import pandas as pd
import numpy as np
from typing import List


def create_demand_features(df: pd.DataFrame, target_col: str = "units_sold") -> pd.DataFrame:
    """
    Transforms raw retail transaction records into an ML-ready feature matrix.
    """
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(by=["product_id", "date"]).reset_index(drop=True)

    # 1. Product & Category Identifiers
    data["product_baseline_sales"] = data.groupby("product_id")[target_col].transform("mean")
    data["product_code"] = data["product_id"].astype("category").cat.codes
    data["category_code"] = data["category"].astype("category").cat.codes

    # 2. Calendar & Temporal Features
    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["quarter"] = data["date"].dt.quarter
    data["is_weekend"] = data["day_of_week"].apply(lambda x: 1 if x in [5, 6] else 0)

    # 3. Promotional & Pricing Elasticity
    if "discount_percent" in data.columns and "unit_price" in data.columns:
        data["price_discount_amount"] = data["unit_price"] * (data["discount_percent"] / 100.0)
    else:
        data["price_discount_amount"] = 0.0

    # 4. Lag Features (Historical demand memory)
    grouped = data.groupby("product_id")[target_col]
    data["lag_1"] = grouped.shift(1)
    data["lag_7"] = grouped.shift(7)
    data["lag_14"] = grouped.shift(14)
    data["lag_30"] = grouped.shift(30)

    # 5. Rolling Window Moving Averages & Volatility
    data["rolling_mean_7"] = grouped.transform(lambda x: x.shift(1).rolling(window=7, min_periods=1).mean())
    data["rolling_std_7"] = grouped.transform(lambda x: x.shift(1).rolling(window=7, min_periods=1).std()).fillna(0)
    data["rolling_mean_30"] = grouped.transform(lambda x: x.shift(1).rolling(window=30, min_periods=1).mean())

    # Fill initial boundary gaps
    fill_cols = ["lag_1", "lag_7", "lag_14", "lag_30", "rolling_mean_7", "rolling_std_7", "rolling_mean_30"]
    for col in fill_cols:
        data[col] = data.groupby("product_id")[col].bfill().ffill().fillna(0)

    return data


def get_feature_columns() -> List[str]:
    """Returns the exact list of predictive feature column names."""
    return [
        "product_baseline_sales",
        "product_code",
        "category_code",
        "unit_price",
        "discount_percent",
        "promotional_campaign",
        "is_holiday",
        "day_of_week",
        "day_of_month",
        "month",
        "quarter",
        "is_weekend",
        "price_discount_amount",
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_std_7",
        "rolling_mean_30"
    ]
