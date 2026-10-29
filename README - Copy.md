# Cloud-Based Product Demand Prediction System

[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Machine Learning](https://img.shields.io/badge/ML-Random%20Forest%20%7C%20R%C2%B2%200.94-green.svg)](https://scikit-learn.org)
[![Cloud Architecture](https://img.shields.io/badge/Cloud-AWS%20Free%20Tier-orange.svg)](#cloud-architecture)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

An enterprise-grade Cloud Computing and Machine Learning supply chain forecasting system. Predicts future product demand using historical sales data, models price elasticity with an interactive What-If simulator, and computes automated replenishment thresholds (Safety Stock, Reorder Point, and EOQ).

---

## Key Highlights

* **High-Accuracy ML Model:** Random Forest Regressor achieving **$R^2 = 0.940$** (94% accuracy) and **$\text{MAE} = \pm 8.6\text{ units}$**.
* **AWS Free-Tier Compliant ($0.00 Cost):** Uses Amazon S3 (5 GB free) and Amazon DynamoDB (25 GB always free) with a built-in offline simulation mode—**no AWS account, subscription, or login required to run**.
* **What-If Scenario Simulator:** Real-time simulation sliders for price discounts (0–40%), promotional campaigns, and holiday surges to evaluate demand elasticity before launching campaigns.
* **Automated Supply Chain Optimization:** Calculates **Safety Stock (SS)**, **Reorder Point (ROP)**, **Economic Order Quantity (EOQ)**, and triggers **Stockout & Overstocking Risk Alerts**.
* **Executive Web Console:** Interactive Chart.js time-series visualizations, KPI cards, drag-and-drop CSV dataset uploader, and cloud architecture modal.

---

## System Architecture

```
User / Web Dashboard (Interactive Forecasts, What-If Simulator)
        │
        ▼ (REST API)
FastAPI Application Server & Gateway
   ┌────┴───────────────────────────────┐
   ▼                                    ▼
Amazon S3 (Historical Datasets)     Machine Learning Pipeline (Random Forest, Lags)
                                        │
                                        ▼ (Predictions & ROP/EOQ Analytics)
                                    Amazon DynamoDB (Forecasts & Stockout Alerts)
```

---

## Quick Start (Run Locally in 2 Steps)

### Step 1: Run the Automated Validation Suite
```powershell
python test_system.py
```
*Validates dataset, feature engineering, Random Forest training ($R^2 = 0.94$), What-If simulations, and cloud endpoints.*

### Step 2: Start the Web Dashboard
```powershell
python run_app.py
```
Open **http://localhost:8000** in your browser:
* Select any product (Smart TV, Headphones, Gaming Laptop, Olive Oil, Coffee, etc.).
* Choose a forecast horizon (7, 14, or 30 days).
* Adjust the price discount slider or toggles to simulate demand lifts.
* Click **"⚡ Run Demand Forecast"** to see live predictions and inventory alerts.

---

## Project Directory Structure

```
product_demand_prediction_aws/
├── app/
│   ├── config.py                 # Multi-cloud & AWS Free-Tier settings
│   ├── main.py                   # FastAPI server (upload, train, predict, inventory APIs)
│   ├── ml/
│   │   ├── feature_engineering.py# Lags (t-1, t-7, t-14), rolling averages, calendar features
│   │   ├── models.py             # Random Forest, Gradient Boosting, Ridge models & forecasting
│   │   └── inventory_math.py     # Safety Stock, Reorder Point, EOQ, Stockout & Overstock math
│   └── cloud/
│       ├── s3_storage.py         # Amazon S3 dataset storage (with local fallback)
│       └── dynamodb_store.py     # Amazon DynamoDB forecast store (with local fallback)
├── data/
│   ├── sample_sales_data.csv     # 5,840 realistic retail sales records (2 years across 8 SKUs)
│   ├── generate_data.py          # Synthetic sales dataset generator
│   └── trained_models/           # Serialized model weights
├── static/
│   ├── index.html                # Executive supply chain dashboard
│   ├── css/styles.css            # Dark enterprise tactical theme
│   └── js/dashboard.js           # Chart.js visualization, what-if sliders, CSV uploader
├── cloud_infra/
│   ├── aws_free_tier/main.tf     # Terraform template for AWS S3 & DynamoDB Free Tier
│   └── docker-compose.yml        # Multi-container orchestration with LocalStack
├── docs/
│   ├── ARCHITECTURE.md           # Complete cloud & ML system architecture specification
│   ├── VIVA_PRESENTATION_GUIDE.md# 3-minute demo script, top 10 viva questions & winning answers
│   └── AWS_FREE_TIER_GUIDE.md    # Guide explaining how AWS Free Tier covers this project for $0
├── test_system.py                # Automated end-to-end integration test runner
├── run_app.py                    # One-click launcher script
├── requirements.txt              # Production dependency manifest
└── Dockerfile                    # Containerization build file
```

---

## Academic & Viva Voce Resources
* For formulas and machine learning mathematical specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
* For presentation scripts, viva questions, and examiner explanations, see [docs/VIVA_PRESENTATION_GUIDE.md](docs/VIVA_PRESENTATION_GUIDE.md).
* For cloud billing and Free Tier breakdown, see [docs/AWS_FREE_TIER_GUIDE.md](docs/AWS_FREE_TIER_GUIDE.md).
