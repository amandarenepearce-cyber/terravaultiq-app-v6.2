TerraVaultIQ Lead Intelligence V6 Update

What is in this update
- Multi-ZIP search flow designed to support up to 1,000 leads in one run
- Enrichment no longer capped at 20 rows in the main flow
- Final result cap options: 100, 250, 500, 1000
- Excel (.xlsx) export for search results and package outputs
- Google Sheets-ready CSV export for search results and package outputs
- Full package ZIP with client and CRM files
- Premium TerraVaultIQ branding shell

How to run
1. Open a terminal in this folder
2. Install dependencies:
   pip install -r requirements.txt
3. Start the app:
   python -m streamlit run app_gui.py

Google Sheets note
- This update includes Google Sheets-ready CSV downloads.
- It does not yet push directly into a live Google Sheet.
- To use in Google Sheets now, either import the CSV or upload the Excel file to Google Drive and open with Sheets.

Important note
- The OpenStreetMap path is enabled out of the box.
- If you want stronger Google business discovery, wire your Google API flow into modules/discovery.py.
