# Deploy with Streamlit Community Cloud (no AWS)

## Run locally

1. Install Python 3.10 or 3.11.
2. Open a terminal in the project root.
3. Create and activate a virtual environment if desired.
4. Install dependencies: `pip install -r requirements.txt`
5. Start the dashboard: `streamlit run streamlit_app.py`
6. Open the local URL printed in the terminal (usually `http://localhost:8501`).

## Deploy online

1. Create/sign in to GitHub and create a repository for this project.
2. Upload the project files, including `streamlit_app.py`, `requirements.txt`, the `app/` directory, and `data/sample_sales_data.csv`.
3. Open https://share.streamlit.io/ and connect GitHub.
4. Choose the repository and branch, and set the main file path to `streamlit_app.py`.
5. Deploy the app. Streamlit Community Cloud will install `requirements.txt` and provide a public app URL.

## Notes

- This Streamlit version does not require AWS credentials or AWS services.
- The included model code is reused. If the saved model file is incompatible with the installed scikit-learn version, delete/retrain the model or pin the matching scikit-learn version.
- Streamlit Community Cloud's local filesystem is not a durable database. Uploaded CSV files and retrained model changes may not persist across restarts or redeployments. Add a hosted database/object store if persistent storage is required.
- Do not commit credentials, API keys, or `.env` secrets to GitHub.
