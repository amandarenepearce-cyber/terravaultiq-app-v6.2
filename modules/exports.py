from __future__ import annotations

import io
import json
import zipfile

import pandas as pd


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.book[sheet_name]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 40)
    buf.seek(0)
    return buf.read()


def build_package_zip_bytes(client_df: pd.DataFrame, crm_df: pd.DataFrame, summary_text: str, manifest: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("client_leads.csv", dataframe_to_csv_bytes(client_df))
        zf.writestr("client_leads.xlsx", dataframe_to_excel_bytes(client_df, sheet_name="Client Leads"))
        zf.writestr("crm_import.csv", dataframe_to_csv_bytes(crm_df))
        zf.writestr("crm_import.xlsx", dataframe_to_excel_bytes(crm_df, sheet_name="CRM Import"))
        zf.writestr("package_summary.txt", summary_text.encode("utf-8"))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    buf.seek(0)
    return buf.read()
