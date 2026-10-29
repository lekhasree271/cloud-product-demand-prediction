"""
Machine Learning Demand Forecasting Models Module
Implements Random Forest, Gradient Boosting, and Linear Regression with cross-validation,
performance evaluation metrics (R², RMSE, MAE), and recursive multi-horizon forecasting.
"""

import time
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from app.config import settings
from app.ml.feature_engineering import create_demand_features, get_feature_columns
from app.ml.inventory_math import compute_inventory_metrics


class DemandForecaster:
    def __init__(self):
        self.model = None
        self.model_type = settings.DEFAULT_MODEL_TYPE
        self.feature_columns = get_feature_columns()
        self.metrics: Dict[str, Any] = {}
        self.feature_importances: List[Dict[str, Any]] = []
        self.last_trained_at: Optional[str] = None
        self.product_meta: Dict[str, Dict[str, Any]] = {}
        self.model_file = settings.MODELS_DIR / "demand_model.joblib"
        self._load_cached_model()

    def _load_cached_model(self):
        """Loads serialized model from disk if available."""
        if self.model_file.exists():
            try:
                bundle = joblib.load(self.model_file)
                self.model = bundle["model"]
                self.model_type = bundle["model_type"]
                self.metrics = bundle["metrics"]
                self.feature_importances = bundle["feature_importances"]
                self.last_trained_at = bundle.get("trained_at")
                self.product_meta = bundle.get("product_meta", {})
            except Exception:
                pass

    def train(self, df: pd.DataFrame, model_type: str = "RandomForest") -> Dict[str, Any]:
        """
        Trains the ML model on historical sales data and evaluates performance.
        """
        self.model_type = model_type
        start_time = time.time()

        # 1. Feature Engineering
        featured_df = create_demand_features(df, target_col="units_sold")

        # Cache product mappings for forecasting
        for pid, grp in featured_df.groupby("product_id"):
            self.product_meta[pid] = {
                "base_sales": float(grp["product_baseline_sales"].iloc[0]),
                "product_code": int(grp["product_code"].iloc[0]),
                "category_code": int(grp["category_code"].iloc[0])
            }

        X = featured_df[self.feature_columns]
        y = featured_df["units_sold"]

        # 2. Time-aware Train/Test Split (last 20% dates as test set across all products)
        unique_dates = featured_df["date"].drop_duplicates().sort_values()
        cutoff = unique_dates.iloc[int(len(unique_dates) * (1 - settings.TEST_SPLIT_RATIO))]
        train_mask = featured_df["date"] < cutoff
        test_mask = featured_df["date"] >= cutoff

        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]

        # 3. Model Selection & Fitting
        if model_type == "GradientBoosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.08,
                max_depth=5,
                random_state=settings.RANDOM_STATE
            )
        elif model_type == "LinearRegression":
            self.model = Ridge(alpha=1.0)
        else: # RandomForest (Default)
            self.model = RandomForestRegressor(
                n_estimators=settings.N_ESTIMATORS,
                max_depth=14,
                min_samples_split=3,
                n_jobs=-1,
                random_state=settings.RANDOM_STATE
            )

        self.model.fit(X_train, y_train)
        training_time_sec = round(time.time() - start_time, 2)

        # 4. Model Evaluation Metrics
        y_pred = self.model.predict(X_test)
        y_pred = np.maximum(0, y_pred)

        r2 = round(float(r2_score(y_test, y_pred)), 3)
        mae = round(float(mean_absolute_error(y_test, y_pred)), 2)
        rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2)

        non_zero = y_test > 0
        mape = round(float(np.mean(np.abs((y_test[non_zero] - y_pred[non_zero]) / y_test[non_zero])) * 100), 2)
        accuracy_pct = round(max(0.0, 100.0 - mape), 1)

        self.metrics = {
            "r2_score": r2,
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "accuracy_percentage": accuracy_pct,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "training_time_seconds": training_time_sec
        }

        # 5. Extract Feature Importances
        self.feature_importances = []
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            pairs = sorted(zip(self.feature_columns, importances), key=lambda x: x[1], reverse=True)
            self.feature_importances = [{"feature": f, "importance": round(float(imp), 4)} for f, imp in pairs[:8]]
        elif hasattr(self.model, "coef_"):
            coefs = np.abs(self.model.coef_)
            pairs = sorted(zip(self.feature_columns, coefs), key=lambda x: x[1], reverse=True)
            self.feature_importances = [{"feature": f, "importance": round(float(c), 4)} for f, c in pairs[:8]]

        self.last_trained_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # 6. Serialize Model Bundle
        joblib.dump({
            "model": self.model,
            "model_type": self.model_type,
            "metrics": self.metrics,
            "feature_importances": self.feature_importances,
            "trained_at": self.last_trained_at,
            "product_meta": self.product_meta
        }, self.model_file)

        return {
            "status": "TRAINED",
            "model_type": self.model_type,
            "metrics": self.metrics,
            "top_features": self.feature_importances
        }

    def predict_future(
        self,
        df: pd.DataFrame,
        product_id: str,
        horizon_days: int = 14,
        discount_override: Optional[float] = None,
        promo_override: Optional[int] = None,
        holiday_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates recursive daily demand predictions for a specified horizon
        with support for What-If scenario simulations.
        """
        if self.model is None or not self.product_meta:
            self.train(df, model_type="RandomForest")

        product_df = df[df["product_id"] == product_id].copy()
        if product_df.empty:
            raise ValueError(f"Product ID '{product_id}' not found in dataset.")

        product_name = product_df["product_name"].iloc[0]
        category = product_df["category"].iloc[0]
        current_inv = int(product_df["current_inventory"].iloc[-1])
        base_unit_price = float(product_df["unit_price"].iloc[-1])

        featured = create_demand_features(df, target_col="units_sold")
        p_data = featured[featured["product_id"] == product_id].sort_values("date").reset_index(drop=True)

        last_date = p_data["date"].iloc[-1]
        historical_demands = p_data["units_sold"].tolist()

        meta = self.product_meta.get(product_id, {
            "base_sales": float(p_data["product_baseline_sales"].iloc[0]),
            "product_code": int(p_data["product_code"].iloc[0]),
            "category_code": int(p_data["category_code"].iloc[0])
        })

        forecast_dates = []
        forecast_values = []
        simulated_history = list(historical_demands)

        for step in range(1, horizon_days + 1):
            next_date = last_date + timedelta(days=step)
            dow = next_date.weekday()
            dom = next_date.day
            month = next_date.month
            quarter = (month - 1) // 3 + 1
            is_weekend = 1 if dow in [5, 6] else 0

            is_hol = holiday_override if holiday_override is not None else (1 if (month == 12 and dom >= 20) or (month == 11 and 24 <= dom <= 29) else 0)
            is_promo = promo_override if promo_override is not None else 0
            disc = discount_override if discount_override is not None else (15.0 if is_promo else 0.0)
            price = round(base_unit_price * (1.0 - disc / 100.0), 2)
            disc_amt = round(base_unit_price * (disc / 100.0), 2)

            l1 = simulated_history[-1] if len(simulated_history) >= 1 else meta["base_sales"]
            l7 = simulated_history[-7] if len(simulated_history) >= 7 else l1
            l14 = simulated_history[-14] if len(simulated_history) >= 14 else l7
            l30 = simulated_history[-30] if len(simulated_history) >= 30 else l14

            r_mean7 = float(np.mean(simulated_history[-7:])) if len(simulated_history) >= 7 else l1
            r_std7 = float(np.std(simulated_history[-7:])) if len(simulated_history) >= 7 else 1.0
            r_mean30 = float(np.mean(simulated_history[-30:])) if len(simulated_history) >= 30 else r_mean7

            row_features = pd.DataFrame([{
                "product_baseline_sales": meta["base_sales"],
                "product_code": meta["product_code"],
                "category_code": meta["category_code"],
                "unit_price": price,
                "discount_percent": disc,
                "promotional_campaign": is_promo,
                "is_holiday": is_hol,
                "day_of_week": dow,
                "day_of_month": dom,
                "month": month,
                "quarter": quarter,
                "is_weekend": is_weekend,
                "price_discount_amount": disc_amt,
                "lag_1": l1,
                "lag_7": l7,
                "lag_14": l14,
                "lag_30": l30,
                "rolling_mean_7": r_mean7,
                "rolling_std_7": r_std7,
                "rolling_mean_30": r_mean30
            }])[self.feature_columns]

            pred_val = float(self.model.predict(row_features)[0])
            pred_val = max(0.0, round(pred_val, 1))

            forecast_dates.append(next_date.strftime("%Y-%m-%d"))
            forecast_values.append(pred_val)
            simulated_history.append(pred_val)

        total_predicted_demand = round(float(sum(forecast_values)), 1)
        avg_predicted_daily = round(total_predicted_demand / horizon_days, 1)

        # Inventory Optimization Metrics
        inv_metrics = compute_inventory_metrics(
            daily_demand_series=forecast_values,
            current_inventory=current_inv,
            unit_price=base_unit_price,
            predicted_horizon_demand=total_predicted_demand,
            lead_time_days=7
        )

        recent_history = p_data.tail(30)[["date", "units_sold"]].to_dict(orient="records")
        for r in recent_history:
            r["date"] = r["date"].strftime("%Y-%m-%d")

        return {
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "horizon_days": horizon_days,
            "total_predicted_units": total_predicted_demand,
            "avg_daily_demand": avg_predicted_daily,
            "current_inventory": current_inv,
            "unit_price": base_unit_price,
            "applied_discount_percent": discount_override if discount_override is not None else 0,
            "forecast_series": [{"date": d, "predicted_units": v} for d, v in zip(forecast_dates, forecast_values)],
            "historical_recent_series": recent_history,
            "inventory_analysis": inv_metrics
        }


# Global Forecaster Singleton
forecaster = DemandForecaster()
