import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)
start_date = datetime(2024, 1, 1)
days = 365 * 2  # 2 years of daily data
date_range = [start_date + timedelta(days=i) for i in range(days)]

products = [
    {'id': 'PROD_001', 'name': 'Ultra HD Smart TV 55-inch', 'category': 'Electronics', 'base_price': 499.99, 'base_demand': 18, 'inv': 65},
    {'id': 'PROD_002', 'name': 'Wireless Noise-Canceling Headphones', 'category': 'Electronics', 'base_price': 149.99, 'base_demand': 45, 'inv': 140},
    {'id': 'PROD_003', 'name': 'Ergonomic Gaming Laptop 16GB', 'category': 'Electronics', 'base_price': 899.99, 'base_demand': 12, 'inv': 35},
    {'id': 'PROD_004', 'name': 'Organic Cold-Pressed Olive Oil 1L', 'category': 'Groceries', 'base_price': 24.99, 'base_demand': 85, 'inv': 210},
    {'id': 'PROD_005', 'name': 'Artisan Roast Arabica Coffee 1kg', 'category': 'Groceries', 'base_price': 19.99, 'base_demand': 110, 'inv': 320},
    {'id': 'PROD_006', 'name': 'Thermal Winter Down Jacket', 'category': 'Apparel', 'base_price': 129.99, 'base_demand': 30, 'inv': 95},
    {'id': 'PROD_007', 'name': 'Breathable Mesh Running Shoes', 'category': 'Apparel', 'base_price': 79.99, 'base_demand': 55, 'inv': 160},
    {'id': 'PROD_008', 'name': 'Liposomal Vitamin C 1000mg', 'category': 'Healthcare', 'base_price': 29.99, 'base_demand': 70, 'inv': 190}
]

records = []
for p in products:
    for d in date_range:
        day_of_week = d.weekday()  # 0-6
        month = d.month
        
        # Weekend boost (Thur-Sat shopping surge)
        weekend_boost = 1.35 if day_of_week in [4, 5, 6] else 1.0
        
        # Seasonality
        if p['category'] == 'Apparel' and 'Winter' in p['name']:
            seasonal_factor = 2.4 if month in [11, 12, 1, 2] else 0.4
        elif p['category'] == 'Electronics':
            seasonal_factor = 1.8 if month in [11, 12] else (1.3 if month in [7, 8] else 1.0)
        else:
            seasonal_factor = 1.1 if month in [6, 7, 8, 12] else 1.0
            
        # Holidays (New Year, Black Friday, Christmas)
        is_holiday = 1 if (month == 12 and d.day >= 20) or (month == 11 and d.day >= 24 and d.day <= 29) or (month == 1 and d.day == 1) else 0
        holiday_boost = 1.6 if is_holiday else 1.0
        
        # Promotions (12% chance)
        is_promo = 1 if np.random.rand() < 0.12 else 0
        discount = np.random.choice([0.10, 0.15, 0.20, 0.25]) if is_promo else 0.0
        discount_boost = 1.0 + (discount * 2.8)  # price elasticity
        
        # Calculate daily units sold
        expected_demand = p['base_demand'] * weekend_boost * seasonal_factor * holiday_boost * discount_boost
        actual_demand = max(0, int(np.random.poisson(expected_demand) + np.random.normal(0, 1.5)))
        
        actual_price = round(p['base_price'] * (1 - discount), 2)
        
        records.append({
            'date': d.strftime('%Y-%m-%d'),
            'product_id': p['id'],
            'product_name': p['name'],
            'category': p['category'],
            'units_sold': actual_demand,
            'unit_price': actual_price,
            'discount_percent': int(discount * 100),
            'promotional_campaign': is_promo,
            'is_holiday': is_holiday,
            'current_inventory': p['inv']
        })

df = pd.DataFrame(records)
out_dir = Path(r"c:\Users\Admin\Downloads\product_demand_prediction_aws\data")
out_dir.mkdir(parents=True, exist_ok=True)
csv_path = out_dir / "sample_sales_data.csv"
df.to_csv(csv_path, index=False)
print(f"Generated {len(df)} realistic retail sales records at: {csv_path}")
