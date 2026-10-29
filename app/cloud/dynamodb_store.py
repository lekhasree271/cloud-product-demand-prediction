"""
AWS DynamoDB Cloud Database Module (Free Tier Compliant)
Persists demand predictions, inventory thresholds (ROP, EOQ), and overstock/stockout alerts.
Includes zero-login local simulation fallback using an ACID SQLite document store.
"""

import json
import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger("DemandForecast.DynamoDB")


class DynamoDBStore:
    def __init__(self):
        self.table_name = settings.DYNAMODB_TABLE_NAME
        self.region = settings.AWS_REGION
        self.has_credentials = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        self.db_path = settings.SQLITE_PATH
        self.dynamo_table = None

        if self.has_credentials:
            try:
                import boto3
                dynamodb = boto3.resource(
                    "dynamodb",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                self.dynamo_table = dynamodb.Table(self.table_name)
                logger.info(f"Connected to AWS DynamoDB Table: {self.table_name}")
            except Exception as e:
                logger.warning(f"DynamoDB connection failed ({e}). Falling back to Local Store.")
                self.has_credentials = False

        self._init_local_db()

    def _init_local_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                horizon_days INTEGER NOT NULL,
                total_predicted_units REAL NOT NULL,
                current_inventory INTEGER NOT NULL,
                reorder_point INTEGER NOT NULL,
                recommended_eoq INTEGER NOT NULL,
                stockout_risk_pct REAL NOT NULL,
                overstock_risk_pct REAL NOT NULL,
                forecast_data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_alerts (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_forecast(self, forecast: Dict[str, Any]) -> str:
        rec_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        inv = forecast.get("inventory_analysis", {})

        # Save to AWS DynamoDB if live credentials configured
        if self.has_credentials and self.dynamo_table:
            try:
                from decimal import Decimal
                item = {
                    "id": rec_id,
                    "timestamp": ts,
                    "product_id": forecast["product_id"],
                    "product_name": forecast["product_name"],
                    "total_predicted_units": Decimal(str(forecast["total_predicted_units"])),
                    "current_inventory": int(forecast["current_inventory"]),
                    "reorder_point": int(inv.get("reorder_point", 0)),
                    "eoq": int(inv.get("recommended_order_quantity_eoq", 0)),
                    "stockout_risk": Decimal(str(inv.get("stockout_risk", {}).get("risk_percentage", 0))),
                    "cloud_provider": "AWS_DYNAMODB_FREE_TIER"
                }
                self.dynamo_table.put_item(Item=item)
            except Exception as e:
                logger.error(f"DynamoDB PutItem error: {e}")

        # Always persist to local SQLite store for instant dashboard retrieval
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO forecasts (
                id, product_id, product_name, category, horizon_days,
                total_predicted_units, current_inventory, reorder_point,
                recommended_eoq, stockout_risk_pct, overstock_risk_pct, forecast_data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec_id,
            forecast["product_id"],
            forecast["product_name"],
            forecast.get("category", "General"),
            forecast["horizon_days"],
            forecast["total_predicted_units"],
            forecast["current_inventory"],
            inv.get("reorder_point", 0),
            inv.get("recommended_order_quantity_eoq", 0),
            inv.get("stockout_risk", {}).get("risk_percentage", 0.0),
            inv.get("overstock_risk", {}).get("risk_percentage", 0.0),
            json.dumps(forecast.get("forecast_series", []))
        ))

        # Check and log alert if needed
        stockout = inv.get("stockout_risk", {})
        if stockout.get("status") in ("CRITICAL_STOCKOUT_RISK", "REORDER_TRIGGERED"):
            alert_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO inventory_alerts (id, product_id, product_name, alert_type, urgency, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                forecast["product_id"],
                forecast["product_name"],
                "STOCKOUT_WARNING",
                stockout.get("urgency", "HIGH"),
                stockout.get("message", "Reorder required.")
            ))

        overstock = inv.get("overstock_risk", {})
        if overstock.get("status") == "EXCESS_OVERSTOCK":
            alert_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO inventory_alerts (id, product_id, product_name, alert_type, urgency, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                forecast["product_id"],
                forecast["product_name"],
                "OVERSTOCK_WARNING",
                "MEDIUM",
                overstock.get("message", "Excess stock detected.")
            ))

        conn.commit()
        conn.close()
        return rec_id

    def list_recent_forecasts(self, limit: int = 25) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM forecasts ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def list_alerts(self, limit: int = 15) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM inventory_alerts ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def clear_all(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM forecasts")
        cur.execute("DELETE FROM inventory_alerts")
        conn.commit()
        conn.close()


# Global DynamoDB Singleton
dynamodb_store = DynamoDBStore()
