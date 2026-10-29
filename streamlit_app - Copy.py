"""Streamlit interface for the Product Demand Prediction System (no AWS required)."""
from pathlib import Path
import io
import pandas as pd
import streamlit as st

from app.ml.models import DemandForecaster

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "data" / "sample_sales_data.csv"

st.set_page_config(page_title="Product Demand Prediction", page_icon="📦", layout="wide")

@st.cache_resource
def get_forecaster():
    return DemandForecaster()

@st.cache_data
def load_default_data():
    df = pd.read_csv(DEFAULT_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    return df

st.title("📦 Product Demand Prediction System")
st.caption("Machine-learning demand forecasting and inventory recommendations — powered by Streamlit, Python and scikit-learn. No AWS required.")

with st.sidebar:
    st.header("Data and model")
    uploaded_file = st.file_uploader("Upload sales data (CSV, optional)", type=["csv"])
    st.caption("Required columns: date, product_id, product_name, units_sold, unit_price. Optional columns used by inventory views include category and current_inventory.")

try:
    if uploaded_file is not None:
        df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
        required = {"date", "product_id", "product_name", "units_sold", "unit_price"}
        missing = required - set(df.columns)
        if missing:
            st.error("CSV is missing required columns: " + ", ".join(sorted(missing)))
            st.stop()
        if "category" not in df.columns:
            df["category"] = "Uncategorized"
        if "current_inventory" not in df.columns:
            st.error("CSV must also include current_inventory for inventory recommendations.")
            st.stop()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        df = df.dropna(subset=["date", "product_id", "product_name", "units_sold", "unit_price"])
        if df.empty:
            st.error("No valid rows found in the uploaded CSV.")
            st.stop()
        df["product_id"] = df["product_id"].astype(str)
    else:
        df = load_default_data().copy()
        df["product_id"] = df["product_id"].astype(str)

    if df.empty:
        st.warning("The dataset contains no records.")
        st.stop()

    # Dataset overview
    product_count = df["product_id"].nunique()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales records", f"{len(df):,}")
    c2.metric("Products", f"{product_count:,}")
    c3.metric("Total units sold", f"{df['units_sold'].sum():,.0f}")
    c4.metric("Date range", f"{df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")

    st.subheader("Historical sales overview")
    daily = df.groupby("date", as_index=False)["units_sold"].sum().sort_values("date")
    st.line_chart(daily.set_index("date")["units_sold"], y_label="Units sold", x_label="Date")

    st.subheader("Generate a demand forecast")
    product_rows = df.sort_values("date").groupby("product_id").tail(1).drop_duplicates("product_id")
    product_rows = product_rows.sort_values("product_id")
    product_labels = {
        str(row.product_id): f"{row.product_id} — {row.product_name}"
        for row in product_rows.itertuples()
    }
    selected_id = st.selectbox("Select product", list(product_labels), format_func=lambda x: product_labels[x])
    col1, col2, col3 = st.columns(3)
    with col1:
        horizon = st.slider("Forecast horizon (days)", min_value=1, max_value=60, value=14)
    with col2:
        discount = st.slider("Discount (%)", min_value=0, max_value=80, value=0)
    with col3:
        promo = st.selectbox("Promotional campaign", ["No", "Yes"])
    holiday = st.selectbox("Holiday period", ["Automatic", "No", "Yes"], index=0)

    model_type = st.selectbox("Model algorithm", ["RandomForest", "GradientBoosting", "LinearRegression"])
    if st.button("Train / Update Model", type="secondary"):
        with st.spinner("Training model on the selected dataset..."):
            result = get_forecaster().train(df, model_type=model_type)
        st.session_state["last_training"] = result
        st.success(f"Model trained: {result['model_type']}")

    if "last_training" in st.session_state:
        metrics = st.session_state["last_training"].get("metrics", {})
        if metrics:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("R² score", metrics.get("r2_score", "—"))
            m2.metric("MAE", metrics.get("mae", "—"))
            m3.metric("RMSE", metrics.get("rmse", "—"))
            m4.metric("Estimated accuracy", f"{metrics.get('accuracy_percentage', '—')}%")

    if st.button("Predict Demand", type="primary"):
        try:
            forecaster = get_forecaster()
            if forecaster.model is None or not forecaster.product_meta:
                with st.spinner("Training the model for the first time..."):
                    forecaster.train(df, model_type=model_type)
            holiday_override = None if holiday == "Automatic" else (1 if holiday == "Yes" else 0)
            with st.spinner("Generating forecast and inventory recommendations..."):
                forecast = forecaster.predict_future(
                    df=df,
                    product_id=selected_id,
                    horizon_days=horizon,
                    discount_override=float(discount) if discount else None,
                    promo_override=1 if promo == "Yes" else 0,
                    holiday_override=holiday_override,
                )
            st.session_state["last_forecast"] = forecast
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")

    forecast = st.session_state.get("last_forecast")
    if forecast:
        st.divider()
        st.subheader(f"Forecast results: {forecast['product_name']}")
        a, b, c, d = st.columns(4)
        a.metric("Predicted units", f"{forecast['total_predicted_units']:,.1f}")
        b.metric("Average daily demand", f"{forecast['avg_daily_demand']:,.1f}")
        c.metric("Current inventory", f"{forecast['current_inventory']:,}")
        d.metric("Forecast period", f"{forecast['horizon_days']} days")

        series = pd.DataFrame(forecast["forecast_series"])
        series["date"] = pd.to_datetime(series["date"])
        st.line_chart(series.set_index("date")["predicted_units"], y_label="Predicted units", x_label="Date")
        st.dataframe(series, use_container_width=True, hide_index=True)
        st.download_button("Download forecast CSV", data=series.to_csv(index=False).encode("utf-8"), file_name=f"forecast_{forecast['product_id']}.csv", mime="text/csv")

        inventory = forecast["inventory_analysis"]
        st.subheader("Inventory recommendations")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Safety stock", inventory["safety_stock"])
        i2.metric("Reorder point", inventory["reorder_point"])
        i3.metric("Recommended order quantity (EOQ)", inventory["recommended_order_quantity_eoq"])
        i4.metric("Days of supply", inventory["days_of_supply"])
        risk1, risk2 = st.columns(2)
        with risk1:
            st.markdown("**Stockout risk**")
            st.metric("Risk", f"{inventory['stockout_risk']['risk_percentage']}%", inventory["stockout_risk"]["status"])
            st.write(inventory["stockout_risk"]["message"])
        with risk2:
            st.markdown("**Overstock risk**")
            st.metric("Risk", f"{inventory['overstock_risk']['risk_percentage']}%", inventory["overstock_risk"]["status"])
            st.write(inventory["overstock_risk"]["message"])

    st.divider()
    st.caption("Cloud deployment note: Streamlit Community Cloud hosts this app. This starter version uses the repository dataset and local model files; uploaded data and generated results are not guaranteed to persist across cloud restarts. Use a hosted database or object storage for durable cloud persistence.")
except FileNotFoundError:
    st.error("Default dataset not found. Ensure data/sample_sales_data.csv is included in the project repository.")
except Exception as exc:
    st.exception(exc)
