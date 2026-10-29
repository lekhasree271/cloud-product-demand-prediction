# AWS Free-Tier & Subscription-Free Deployment Guide

This guide details how the **Cloud-Based Product Demand Prediction System** operates within the **AWS Free Tier** with zero cloud billing ($0.00 cost) and how to run it offline without requiring an AWS account or subscription.

---

## 1. AWS Free Tier Breakdown for this Project

| AWS Service | Project Role | AWS Free Tier Allocation | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Amazon S3** | Historical Sales Datasets & Models | **5 GB** Standard Storage for 12 Months | **$0.00** |
| **Amazon DynamoDB** | Demand Forecasts & Stockout Alerts | **25 GB** Storage + 25 WCU / 25 RCU (**Always Free**) | **$0.00** |
| **AWS Lambda** | Serverless ML Inference Execution | **1,000,000 Requests/Month** (**Always Free**) | **$0.00** |
| **Amazon CloudWatch**| System Metrics & Alarms | **10 Custom Metrics** (**Always Free**) | **$0.00** |

---

## 2. Zero-Login Offline Mode (No AWS Account Needed)

You do **not** need to sign up for AWS or provide credit card information to run and evaluate this project:
* The system is pre-configured with a **Dual-Mode Cloud Abstraction Layer**.
* When no AWS keys are specified in `.env`, the system automatically activates the **Local S3 Object Store** (`data/s3_bucket/`) and **Local DynamoDB NoSQL Store** (`data/forecasts_store.db`).
* The web console displays full AWS cloud metadata and API responses while running locally at microsecond speed with 100% privacy and zero charges.

---

## 3. Optional: Deploying to Live AWS Account

If you do have an active AWS account and wish to deploy to live cloud infrastructure:

### Step 3.1: Configure Environment Variables
Create a `.env` file in the project root:
```env
CLOUD_PROVIDER=AWS_FREE_TIER
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY
S3_BUCKET_NAME=demand-forecasting-sales-data
DYNAMODB_TABLE_NAME=ProductDemandForecasts
```

### Step 3.2: Provision Resources using Terraform
Navigate to the Terraform folder and run:
```bash
cd cloud_infra/aws_free_tier
terraform init
terraform plan
terraform apply -auto-approve
```
This automatically provisions the encrypted S3 bucket and DynamoDB table within Free Tier thresholds.
