# Viva Voce & College Defense Presentation Guide

**Project:** Cloud-Based Product Demand Prediction System  
**Domains:** Cloud Computing · Machine Learning · Cloud Architecture

---

## 1. 3-Minute Demonstration Script for Examiners

1. **Introduction (30 Seconds):**
   > *"Good morning, esteemed examiners. My project is a Cloud-Based Product Demand Prediction System. Traditional stores struggle with two major issues: running out of high-demand items (stockout) and ordering too many low-demand items (overstocking). Our system uses machine learning (Random Forest) deployed on an AWS Free-Tier architecture to predict future customer demand, calculate exact reorder points, and alert retailers in real time."*

2. **Dashboard Demonstration (90 Seconds):**
   * **Show Catalog:** Point out the 8 products across 4 categories (Electronics, Groceries, Apparel, Health) with 5,840 historical daily records.
   * **Show Forecast:** Select **"Ultra HD Smart TV"**, select **14 Days**, and click **"Run Demand Forecast"**. Show the line chart displaying historical demand seamlessly connecting to the future predicted demand line.
   * **Show Inventory Panel:** Explain the **Safety Stock (21 units)**, **Reorder Point (205 units)**, and **Economic Order Quantity (220 units)**. Point out the Stockout Alert when on-hand inventory is lower than ROP.
   * **Demonstrate What-If Simulator:** Move the **Price Discount Slider** from 0% to **25%** and click **Run Demand Forecast**. Point out that demand increased by **+131%** due to price elasticity modeling.
   * **Show Algorithm Selector:** Switch to **Gradient Boosting** or **Linear Regression** and show the $R^2$ score update live.

3. **Cloud Architecture & Free Tier (60 Seconds):**
   * Open the **"Cloud Architecture"** modal.
   * Explain: *Amazon S3 stores the historical sales datasets, Amazon DynamoDB stores the demand predictions and stockout alerts, and the FastAPI application runs the ML inference. This architecture complies 100% with AWS Free Tier, costing $0.00 and running offline without requiring a paid subscription or credit card."*

---

## 2. Top 10 Viva Questions & Winning Answers

### Q1: Why did you choose Random Forest over simple Linear Regression?
**Answer:** *Linear regression assumes a linear relationship between features and demand. However, retail demand has complex non-linear patterns, such as holiday shopping spikes, weekend surges, and non-linear price elasticity. Random Forest is an ensemble of decision trees that captures non-linear interactions without overfitting, achieving an $R^2$ score of 0.94 compared to 0.72 for Linear Regression.*

### Q2: How does your system operate without an AWS subscription or login?
**Answer:** *The project implements a Dual-Mode Cloud Abstraction Pattern. When live AWS credentials are provided, it connects to live Amazon S3 and DynamoDB. When running offline or in development, it activates an AWS Free-Tier Local Simulation Layer that emulates S3 object storage and DynamoDB NoSQL tables locally. This guarantees zero cloud bills ($0.00) while maintaining the exact same cloud API contracts.*

### Q3: What is the difference between Safety Stock and Reorder Point?
**Answer:**
* **Safety Stock ($SS$):** The extra buffer inventory held to protect against unexpected demand surges or supplier shipping delays. Formula: $SS = Z \times \sigma_d \times \sqrt{L}$.
* **Reorder Point ($ROP$):** The specific inventory level that triggers a purchase order. It includes the expected demand during supplier lead time plus the safety stock buffer. Formula: $ROP = (\bar{d} \times L) + SS$.

### Q4: What does the $R^2$ score of 0.94 mean?
**Answer:** *The $R^2$ (coefficient of determination) score of 0.94 means that 94% of the variance in retail sales volume is successfully explained and predicted by our model's features (historical lags, day of week, promotions, and seasonality). The remaining 6% is random unobserved market noise.*

### Q5: What is Mean Absolute Error (MAE) and what was your result?
**Answer:** *MAE measures the average absolute difference between predicted sales and actual sales. Our model achieves an MAE of $\pm 8.6\text{ units}$, meaning on any given day, our demand prediction is off by an average of fewer than 9 units.*

### Q6: What are time-series lag features and why are they necessary?
**Answer:** *Lag features provide the model with historical memory. For example, `lag_1` is yesterday's sales, and `lag_7` is the sales volume on the exact same day last week. In retail, weekly seasonality is strong (e.g. Saturday sales are similar to last Saturday's sales), making `lag_7` one of our top 3 predictive features.*

### Q7: What is Economic Order Quantity (EOQ)?
**Answer:** *EOQ is a classic operations research formula that balances the cost of placing an order against the cost of storing inventory. Ordering in bulk saves on shipping but increases warehouse holding costs. EOQ identifies the exact batch size ($Q^*$) that minimizes total inventory costs.*

### Q8: How does your What-If Scenario Simulator work?
**Answer:** *The What-If simulator allows supply chain managers to test promotional strategies before launching them. When the user adjusts the discount slider to 20%, the system recalculates discounted price variables, adjusts price elasticity features, and feeds them into the trained Random Forest model to project the resulting sales lift and inventory depletion rate.*

### Q9: How can this system scale to thousands of products?
**Answer:** *In production AWS deployment, the FastAPI application can be deployed as serverless AWS Lambda functions behind an API Gateway, with sales datasets partitioned in S3 and forecasts queried via DynamoDB indexes, easily scaling to handle thousands of concurrent queries with sub-second latency.*

### Q10: Can a user upload their own store's data?
**Answer:** *Yes. The dashboard includes a drag-and-drop CSV uploader. When a user uploads a new sales CSV file, it validates the columns, uploads the dataset to Amazon S3, and automatically retrains the Random Forest model on the new dataset within seconds.*
