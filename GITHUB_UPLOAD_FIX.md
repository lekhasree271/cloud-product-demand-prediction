# Fix the Streamlit import error

The repository must preserve this folder structure (do not upload only the files inside the folders):

```text
streamlit_app.py
requirements.txt
app/
  __init__.py
  config.py
  ml/
    __init__.py
    models.py
    feature_engineering.py
    inventory_math.py
  cloud/
    __init__.py
    s3_storage.py
    dynamodb_store.py
data/
  sample_sales_data.csv
  trained_models/
    demand_model.joblib
```

Keep `streamlit_app.py` and `requirements.txt` in the repository root. The import `from app.ml.models import DemandForecaster` requires `app/ml/models.py` to exist in that exact location.
