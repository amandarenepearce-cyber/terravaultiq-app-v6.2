from __future__ import annotations

from datetime import datetime

import pandas as pd

CLIENT_COLUMNS = [
    "name",
    "business_type",
    "search_keyword",
    "source_zip",
    "address",
    "website",
    "primary_email",
    "primary_phone",
    "facebook_link",
    "instagram_link",
    "linkedin_link",
    "rating",
    "ratings_total",
    "lead_score",
    "lead_tier",
    "priority",
    "offer_angle",
    "website_notes",
    "contact_confidence",
]

CRM_COLUMNS = [
    "name",
    "primary_email",
    "primary_phone",
    "website",
    "status",
    "priority",
    "owner",
    "notes",
    "offer_angle",
    "follow_up_date",
]


def normalize_zip_list(text: str) -> list[str]:
    raw = [part.strip() for part in str(text).replace("\n", ",").split(",")]
    return [part for part in raw if part]


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = ""
    return out[columns].copy()


def build_client_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = _ensure_columns(df, CLIENT_COLUMNS)
    return out.sort_values(by=["lead_score", "name"], ascending=[False, True], na_position="last").reset_index(drop=True)


def build_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in CRM_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out["status"] = out["status"].replace("", "new")
    out["owner"] = out["owner"].replace("", "unassigned")
    return out[CRM_COLUMNS].copy().reset_index(drop=True)


def build_package_summary(df: pd.DataFrame, package_name: str, seller_name: str) -> str:
    total = len(df)
    with_website = int((df.get("website", pd.Series(dtype=str)).astype(str).str.strip() != "").sum()) if total else 0
    with_email = int((df.get("primary_email", pd.Series(dtype=str)).astype(str).str.strip() != "").sum()) if total else 0
    a_tier = int((df.get("lead_tier", pd.Series(dtype=str)).astype(str) == "A").sum()) if total else 0
    return "\n".join([
        f"Package: {package_name}",
        f"Prepared by: {seller_name}",
        f"Prepared on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total leads: {total}",
        f"With website: {with_website}",
        f"With email: {with_email}",
        f"A-tier leads: {a_tier}",
        "Export bundle includes: client CSV, CRM CSV, Excel files, summary, and manifest.",
    ])


def build_package_manifest(df: pd.DataFrame, package_name: str, seller_name: str) -> dict:
    return {
        "package_name": package_name,
        "prepared_by": seller_name,
        "prepared_at": datetime.now().isoformat(),
        "lead_count": int(len(df)),
        "columns": list(df.columns),
        "google_sheets_note": "Use the CSV exports directly in Google Sheets, or upload the Excel file to Drive and open in Sheets.",
    }
