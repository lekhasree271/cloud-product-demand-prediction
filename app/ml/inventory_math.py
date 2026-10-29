"""
Supply Chain & Inventory Optimization Mathematics
Calculates Safety Stock, Reorder Point (ROP), Economic Order Quantity (EOQ),
and automated Stockout & Overstocking risk alerts.
"""

import math
import numpy as np
from typing import Dict, Any
from app.config import settings


def compute_inventory_metrics(
    daily_demand_series: list[float],
    current_inventory: int,
    unit_price: float,
    predicted_horizon_demand: float,
    lead_time_days: int = 7
) -> Dict[str, Any]:
    """
    Computes professional supply chain optimization metrics based on predicted demand.
    
    Args:
        daily_demand_series: Historical or forecasted daily units sold
        current_inventory: Units currently in the warehouse
        unit_price: Selling price per unit in USD
        predicted_horizon_demand: Forecasted demand over upcoming period (e.g., next 14 or 30 days)
        lead_time_days: Supplier replenishment lead time in days (default 7)
        
    Returns:
        Dict of key inventory thresholds, order quantities, and risk alerts.
    """
    if not daily_demand_series:
        daily_demand_series = [10.0]

    mean_daily_demand = float(np.mean(daily_demand_series))
    std_daily_demand = float(np.std(daily_demand_series)) if len(daily_demand_series) > 1 else (mean_daily_demand * 0.25)
    if std_daily_demand <= 0:
        std_daily_demand = max(1.0, mean_daily_demand * 0.15)

    z = settings.SERVICE_LEVEL_Z # 1.65 for 95% service level

    # 1. Safety Stock: SS = Z * sigma_d * sqrt(LeadTime)
    safety_stock = int(math.ceil(z * std_daily_demand * math.sqrt(lead_time_days)))

    # 2. Reorder Point: ROP = (MeanDailyDemand * LeadTime) + SafetyStock
    lead_time_demand = mean_daily_demand * lead_time_days
    reorder_point = int(math.ceil(lead_time_demand + safety_stock))

    # 3. Economic Order Quantity: EOQ = sqrt((2 * D * S) / H)
    annual_demand = max(100.0, mean_daily_demand * 365)
    ordering_cost_s = settings.ORDERING_COST_PER_ORDER # $50 per PO
    holding_cost_h = max(1.0, unit_price * settings.HOLDING_COST_RATE) # 20% carrying cost
    eoq = int(math.ceil(math.sqrt((2 * annual_demand * ordering_cost_s) / holding_cost_h)))

    # 4. Stockout Risk Assessment
    # If on-hand inventory cannot cover the predicted demand during supplier lead time:
    if current_inventory <= safety_stock:
        stockout_risk_pct = 95.0
        stockout_status = "CRITICAL_STOCKOUT_RISK"
        urgency = "URGENT"
    elif current_inventory <= reorder_point:
        stockout_risk_pct = round(min(85.0, 50.0 + (reorder_point - current_inventory) / (reorder_point or 1) * 35.0), 1)
        stockout_status = "REORDER_TRIGGERED"
        urgency = "HIGH"
    else:
        stockout_risk_pct = round(max(5.0, 30.0 - (current_inventory - reorder_point) / (reorder_point or 1) * 20.0), 1)
        stockout_status = "ADEQUATE_STOCK"
        urgency = "NORMAL"

    # 5. Overstocking Risk Assessment (Capital Tied Up)
    # If inventory exceeds 2.5 months of anticipated demand
    monthly_demand = mean_daily_demand * 30.0
    overstock_threshold = int(math.ceil(monthly_demand * 2.2))

    if current_inventory > overstock_threshold:
        excess_units = current_inventory - overstock_threshold
        capital_tied_up = round(excess_units * unit_price, 2)
        overstock_risk_pct = round(min(98.0, 60.0 + (excess_units / (overstock_threshold or 1)) * 40.0), 1)
        overstock_status = "EXCESS_OVERSTOCK"
    else:
        excess_units = 0
        capital_tied_up = 0.0
        overstock_risk_pct = round(max(2.0, (current_inventory / (overstock_threshold or 1)) * 30.0), 1)
        overstock_status = "BALANCED"

    # Days of Inventory Remaining (Runway)
    days_of_supply = round(current_inventory / (mean_daily_demand or 1e-6), 1)

    return {
        "current_inventory": current_inventory,
        "mean_daily_demand": round(mean_daily_demand, 1),
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "recommended_order_quantity_eoq": eoq,
        "days_of_supply": days_of_supply,
        "stockout_risk": {
            "risk_percentage": stockout_risk_pct,
            "status": stockout_status,
            "urgency": urgency,
            "message": (
                f"On-hand inventory ({current_inventory} units) is below Reorder Point ({reorder_point}). Order {eoq} units immediately to avoid stockout."
                if current_inventory <= reorder_point
                else f"Inventory healthy. Estimated {days_of_supply} days of supply remaining."
            )
        },
        "overstock_risk": {
            "risk_percentage": overstock_risk_pct,
            "status": overstock_status,
            "excess_units": excess_units,
            "capital_tied_up_usd": capital_tied_up,
            "message": (
                f"Warning: {excess_units} excess units detected (${capital_tied_up:,} capital tied up). Run targeted promotional discount to liquidate."
                if excess_units > 0
                else "Stock levels well-balanced within lean inventory boundaries."
            )
        }
    }
