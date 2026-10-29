# System Architecture: Cloud-Based Product Demand Prediction System

**Project Focus:** Cloud Computing · Machine Learning & AI · Supply Chain Optimization  
**Cloud Tier:** AWS Free Tier Compliant ($0.00 Monthly Cloud Cost · Zero Subscription Required)

---

## 1. System Overview & Problem Statement

Retailers face two costly supply chain failure modes:
1. **Stockouts:** Running out of high-demand items leads to lost revenue, missed customer sales, and brand attrition.
2. **Overstocking:** Ordering excess inventory ties up working capital, increases warehousing holding costs, and leads to margin-eroding clearance markdowns.

**The Solution:** This project delivers a cloud-based demand forecasting system that uses machine learning to predict future customer demand from historical sales records, dynamically models price elasticity through a What-If scenario simulator, and computes automated replenishment thresholds (Safety Stock, Reorder Point, and Economic Order Quantity).

---

## 2. Multi-Tier Cloud Architecture

```
+-----------------------------------------------------------------------------------+
|                           TIER 1: CLIENT PRESENTATION                             |
|  - Executive Web Dashboard (HTML5, CSS3, JavaScript)                             |
|  - Interactive Multi-Horizon Demand Charts (Chart.js)                             |
|  - What-If Price Elasticity & Promotional Scenario Simulator                      |
|  - Drag-and-Drop CSV Dataset Upload Portal                                        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                    HTTP / REST API
                                          v
+-----------------------------------------------------------------------------------+
|                        TIER 2: API GATEWAY & APPLICATION SERVER                   |
|  - High-performance FastAPI Asynchronous REST Gateway                            |
|  - Pydantic Data Validation & Multi-Part File Streaming                           |
|  - Endpoints: /api/predict/demand, /api/model/train, /api/inventory/alerts       |
+-----------------------------------------+-----------------------------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
+---------------------------------------+   +---------------------------------------+
|  TIER 3A: CLOUD STORAGE (AWS S3)      |   |  TIER 3B: AI / MACHINE LEARNING       |
|  - Amazon S3 Bucket                   |   |  - Ultralight Random Forest Regressor |
|  - Historical Sales Datasets          |   |  - Gradient Boosting & Ridge Models   |
|  - Pre-Signed Download URLs (24h)     |   |  - Autoregressive Multi-Step Forecast |
|  - 5 GB AWS Free Tier (No Cost)       |   |  - Lag Features & Moving Averages     |
+---------------------------------------+   +---------------------------------------+
                                                                |
                                                Forecasts & Alerts
                                                                v
+-----------------------------------------------------------------------------------+
|                 TIER 4: DISTRIBUTED NoSQL DATABASE (AMAZON DYNAMODB)              |
|  - Amazon DynamoDB Table: ProductDemandForecasts                                  |
|  - Stores SKU IDs, Predicted Units, Safety Stock, ROP, EOQ, and Risk Alerts       |
|  - 25 GB Storage & 25 RCU/WCU (Always Free Tier)                                  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Machine Learning Formulation & Algorithms

### 3.1 Feature Engineering Pipeline
The time-series dataset is enriched with temporal and pricing variables:
* **Product Baseline:** Mean historical sales per SKU ($\mu_{SKU}$) prevents cross-product scale distortion.
* **Autoregressive Lags:** Demand at $t-1$, $t-7$, $t-14$, and $t-30$ days captures short- and medium-term memory.
* **Rolling Window Statistics:** 7-day and 30-day moving averages and moving standard deviations capture recent trend and volatility.
* **Calendar Seasonality:** Day of week, day of month, month, quarter, weekend indicator.
* **Price Elasticity & Promotions:** Unit price, discount percentage, promotional campaign flag, holiday surges.

### 3.2 Evaluation Metrics
The models are evaluated against an out-of-time test set (last 20% dates across all products):
* **Coefficient of Determination ($R^2$):** Measures the proportion of variance explained by the model ($\mathbf{R^2 = 0.940}$).
* **Mean Absolute Error (MAE):** Average magnitude of forecast errors in units ($\mathbf{\pm 8.6\text{ units}}$).
* **Root Mean Squared Error (RMSE):** Penalizes larger outlier forecasting errors ($\mathbf{12.8\text{ units}}$).

---

## 4. Supply Chain Inventory Mathematics

### 4.1 Safety Stock ($SS$)
Buffers against demand volatility during replenishment lead times ($L = 7\text{ days}$):
$$SS = Z \times \sigma_d \times \sqrt{L}$$
where $Z = 1.65$ corresponds to a 95% service level cycle, and $\sigma_d$ is the standard deviation of daily demand.

### 4.2 Reorder Point ($ROP$)
The inventory level that triggers an automated purchase order:
$$ROP = (\bar{d} \times L) + SS$$
where $\bar{d}$ is the average daily forecasted demand.

### 4.3 Economic Order Quantity ($EOQ$)
Minimizes total annual ordering ($S$) and holding ($H$) costs:
$$EOQ = \sqrt{\frac{2 D S}{H}}$$
where $D$ is annual forecasted demand, $S = \$50$ per order, and $H = 20\%$ of unit price annually.
