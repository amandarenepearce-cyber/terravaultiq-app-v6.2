import io
import json
import os
from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st
from PIL import Image

from modules.discovery import discover_businesses, search_public_topics, expand_topic_queries
from modules.enrichment import enrich_rows
from modules.scoring import score_rows
from modules.ui_theme import inject_brand_theme
from modules import packager as packager_mod
from modules import exports as exports_mod


# -------------------------------------------------
# Page config + favicon
# -------------------------------------------------
favicon_path = os.path.join("assets", "favicon.png")
page_icon = "🧠"

if os.path.exists(favicon_path):
    try:
        page_icon = Image.open(favicon_path)
    except Exception:
        page_icon = "🧠"

st.set_page_config(
    page_title="TerraVaultIQ",
    page_icon=page_icon,
    layout="wide",
)

inject_brand_theme()


# -------------------------------------------------
# Session state
# -------------------------------------------------
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if "last_run_meta" not in st.session_state:
    st.session_state.last_run_meta = {}


# -------------------------------------------------
# Safe helper bindings / fallbacks
# -------------------------------------------------
def _fallback_normalize_zip_list(text: str) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\n", ",").split(",")]
    return [p for p in parts if p]


normalize_zip_list = getattr(packager_mod, "normalize_zip_list", _fallback_normalize_zip_list)
build_client_export_df = getattr(packager_mod, "build_client_export_df", None)
build_crm_export_df = getattr(packager_mod, "build_crm_export_df", None)
build_package_manifest = getattr(packager_mod, "build_package_manifest", None)
build_package_summary = getattr(packager_mod, "build_package_summary", None)

build_package_zip_bytes = getattr(exports_mod, "build_package_zip_bytes", None)
dataframe_to_excel_bytes = getattr(exports_mod, "dataframe_to_excel_bytes", None)


# -------------------------------------------------
# UI helpers
# -------------------------------------------------
def render_hero():
    st.markdown(
        """
        <div class="tv-hero">
            <div class="tv-pill">TerraVaultIQ • Audience Intelligence Solutions</div>
            <h1>
                Build and activate<br>
                <span class="accent">hyper-targeted<br>audiences</span>
            </h1>
            <p>
                Buy one tool or run the full platform. TerraVaultIQ helps teams build leads,
                create audiences, target by geography, leverage lookback data, and generate
                activation-ready outputs from one connected system.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = ""):
    subtitle_html = f'<div class="tv-card-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="tv-card">
            <h2>{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def default_prompt(search_mode: str):
    defaults = {
        "Marketing Prospect Finder": ("INDUSTRY / CATEGORY", "roofing"),
        "Custom Business Search": ("CATEGORY / KEYWORD", "home cleaning"),
        "Public Intent Search": ("TOPIC / KEYWORD", "need a roofer"),
        "Relocation Interest Finder": ("TARGET AREA", "moving to chicago"),
        "Community Interest Finder": ("COMMUNITY / INTEREST", "small business owners"),
    }
    return defaults.get(search_mode, ("KEYWORD", "roofing"))


def dedupe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    for col in ["name", "address", "website", "phone"]:
        if col not in work.columns:
            work[col] = ""

    work["_dedupe_name"] = work["name"].astype(str).str.strip().str.lower()
    work["_dedupe_address"] = work["address"].astype(str).str.strip().str.lower()
    work["_dedupe_website"] = work["website"].astype(str).str.strip().str.lower()
    work["_dedupe_phone"] = work["phone"].astype(str).str.strip().str.lower()

    work = work.drop_duplicates(
        subset=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"],
        keep="first",
    )

    work = work.drop(
        columns=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"],
        errors="ignore",
    )

    return work.reset_index(drop=True)


def sort_by_score_if_present(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "lead_score" not in df.columns:
        return df.reset_index(drop=True)

    work = df.copy()
    work["_lead_score_num"] = pd.to_numeric(work["lead_score"], errors="coerce").fillna(-1)
    work = work.sort_values("_lead_score_num", ascending=False)
    work = work.drop(columns=["_lead_score_num"], errors="ignore")
    return work.reset_index(drop=True)


def safe_metric_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    s = df[column].astype(str).fillna("").str.strip()
    return int((s != "").sum())


def high_score_count(df: pd.DataFrame) -> int:
    if "lead_score" not in df.columns:
        return 0
    return int((pd.to_numeric(df["lead_score"], errors="coerce").fillna(0) >= 80).sum())


def build_summary_text(
    df: pd.DataFrame,
    package_name: str,
    prepared_by: str,
    search_mode: str,
    keyword: str,
    area_label: str,
) -> str:
    if callable(build_package_summary):
        try:
            return build_package_summary(
                package_name=package_name,
                prepared_by=prepared_by,
                row_count=len(df),
                search_mode=search_mode,
                keyword=keyword,
                area_label=area_label,
            )
        except Exception:
            pass

    lines = [
        f"Package: {package_name}",
        f"Prepared by: {prepared_by}",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Search mode: {search_mode}",
        f"Keyword: {keyword}",
        f"Area label: {area_label}",
        f"Rows included: {len(df)}",
    ]

    if "lead_tier" in df.columns:
        tier_counts = df["lead_tier"].astype(str).value_counts().to_dict()
        lines.append(f"Lead tiers: {tier_counts}")

    if "primary_email" in df.columns:
        lines.append(f"Rows with email: {safe_metric_count(df, 'primary_email')}")
    if "website" in df.columns:
        lines.append(f"Rows with website: {safe_metric_count(df, 'website')}")
    if "primary_phone" in df.columns:
        lines.append(f"Rows with phone: {safe_metric_count(df, 'primary_phone')}")

    lines.extend(
        [
            "",
            "Recommended use:",
            "- Client-ready lead delivery",
            "- Internal sales outreach",
            "- Google Sheets import",
            "- Excel review / QA",
        ]
    )
    return "\n".join(lines)


def fallback_client_export_df(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
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
        "rating",
        "ratings_total",
        "lead_score",
        "lead_tier",
        "priority",
        "offer_angle",
        "website_notes",
    ]
    cols = [c for c in preferred if c in df.columns]
    remainder = [c for c in df.columns if c not in cols]
    return df[cols + remainder].copy()


def fallback_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["name"] = df["name"] if "name" in df.columns else ""
    out["primary_email"] = df["primary_email"] if "primary_email" in df.columns else ""
    out["primary_phone"] = (
        df["primary_phone"]
        if "primary_phone" in df.columns
        else (df["phone"] if "phone" in df.columns else "")
    )
    out["website"] = df["website"] if "website" in df.columns else ""
    out["status"] = "new"
    out["priority"] = df["priority"] if "priority" in df.columns else ""
    out["owner"] = ""
    out["notes"] = df["website_notes"] if "website_notes" in df.columns else ""
    out["offer_angle"] = df["offer_angle"] if "offer_angle" in df.columns else ""
    out["follow_up_date"] = ""
    return out


def get_client_export_df(df: pd.DataFrame) -> pd.DataFrame:
    if callable(build_client_export_df):
        try:
            return build_client_export_df(df)
        except Exception:
            pass
    return fallback_client_export_df(df)


def get_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    if callable(build_crm_export_df):
        try:
            return build_crm_export_df(df)
        except Exception:
            pass
    return fallback_crm_export_df(df)


def dataframe_to_excel_fallback(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    output.seek(0)
    return output.read()


def get_excel_bytes(df: pd.DataFrame) -> bytes:
    if callable(dataframe_to_excel_bytes):
        try:
            return dataframe_to_excel_bytes(df)
        except Exception:
            pass
    return dataframe_to_excel_fallback(df)


def build_manifest(package_name: str, prepared_by: str, row_count: int, meta: dict) -> dict:
    if callable(build_package_manifest):
        try:
            return build_package_manifest(
                package_name=package_name,
                prepared_by=prepared_by,
                row_count=row_count,
                search_mode=meta.get("search_mode", ""),
                keyword=meta.get("keyword", ""),
                area_label=meta.get("area_label", ""),
            )
        except Exception:
            pass

    return {
        "package_name": package_name,
        "prepared_by": prepared_by,
        "generated_at": datetime.now().isoformat(),
        "total_rows": int(row_count),
        "search_mode": meta.get("search_mode", ""),
        "keyword": meta.get("keyword", ""),
        "area_label": meta.get("area_label", ""),
        "exports": [
            "client_leads.csv",
            "crm_import.csv",
            "package_summary.txt",
            "manifest.json",
        ],
    }


def build_package_zip_fallback(
    client_df: pd.DataFrame,
    crm_df: pd.DataFrame,
    summary_text: str,
    manifest: dict,
) -> bytes:
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("client_leads.csv", client_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("crm_import.csv", crm_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("package_summary.txt", summary_text.encode("utf-8"))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    buf.seek(0)
    return buf.read()


def get_package_zip_bytes(
    client_df: pd.DataFrame,
    crm_df: pd.DataFrame,
    summary_text: str,
    manifest: dict,
) -> bytes:
    if callable(build_package_zip_bytes):
        try:
            return build_package_zip_bytes(client_df, crm_df, summary_text, manifest)
        except Exception:
            pass
    return build_package_zip_fallback(client_df, crm_df, summary_text, manifest)


def render_results_card(df: pd.DataFrame, title: str = "Lead Results"):
    render_section_header(title, "Review, score, and export client-ready lead packages.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Results", len(df))
    m2.metric("With Website", safe_metric_count(df, "website"))
    m3.metric("With Email", safe_metric_count(df, "primary_email"))
    m4.metric("High Score", high_score_count(df))

    st.dataframe(df, use_container_width=True, hide_index=True, height=520)


# -------------------------------------------------
# Hero
# -------------------------------------------------
render_hero()

tab1, tab2, tab3 = st.tabs(
    ["Campaign Search", "Client Package Builder", "Expansion Planner"]
)


# -------------------------------------------------
# TAB 1: CAMPAIGN SEARCH
# -------------------------------------------------
with tab1:
    left_col, right_col = st.columns([2.15, 1], gap="large")

    with left_col:
        render_section_header(
            "Location & Keywords",
            "Set the search area, vertical, and campaign discovery inputs.",
        )

        scan_mode = st.radio(
            "Scan Mode",
            ["Single ZIP Deep Scan", "Multi-ZIP Area Scan"],
            index=1,
            horizontal=True,
            key="scan_mode_main",
        )

        if scan_mode == "Single ZIP Deep Scan":
            zip_code = st.text_input("ZIP CODE", value="66048")
            zip_list_text = ""
        else:
            zip_code = ""
            zip_list_text = st.text_area(
                "ZIP LIST",
                value="66048, 66044, 66086",
                height=120,
            )

        radius = st.number_input("RADIUS (miles)", min_value=1, max_value=100, value=10, step=1)
        area_label = st.text_input("CITY / AREA LABEL", value="Leavenworth")

        search_mode = st.selectbox(
            "Search Mode",
            [
                "Marketing Prospect Finder",
                "Custom Business Search",
                "Public Intent Search",
                "Relocation Interest Finder",
                "Community Interest Finder",
            ],
            index=0,
        )

        label, default_value = default_prompt(search_mode)
        category_or_topic = st.text_input(label, value=default_value)

        if search_mode in [
            "Public Intent Search",
            "Relocation Interest Finder",
            "Community Interest Finder",
        ]:
            with st.expander("Suggested public search phrases"):
                for phrase in expand_topic_queries(
                    search_mode,
                    category_or_topic.strip(),
                    zip_code=zip_code.strip(),
                    area_label=area_label.strip(),
                ):
                    st.code(phrase, language=None)

        run_search = st.button("FIND LEADS", use_container_width=True)

    with right_col:
        render_section_header(
            "Search Options",
            "Control enrichment, scoring, fallback search, and final export limits.",
        )

        use_google = st.checkbox("Use Google API if available", value=True)
        use_osm = st.checkbox("Use OpenStreetMap backup", value=False)
        do_enrich = st.checkbox("Find public business contact info", value=True)
        enrich_limit = st.number_input("Max rows to enrich", min_value=0, max_value=5000, value=250, step=50)
        do_score = st.checkbox("Score business leads", value=True)
        trim_results = st.checkbox("Trim final results", value=True)
        final_cap = st.selectbox("Final result cap", [100, 250, 500, 1000], index=3)

        public_pages_only = st.checkbox("Public pages only", value=True)
        max_pages = st.slider("Public search pages", 1, 5, 2)

    if run_search:
        try:
            zips = (
                [zip_code.strip()]
                if scan_mode == "Single ZIP Deep Scan" and zip_code.strip()
                else normalize_zip_list(zip_list_text)
                if scan_mode != "Single ZIP Deep Scan"
                else []
            )

            all_rows = []

            if search_mode in ["Marketing Prospect Finder", "Custom Business Search"]:
                if not zips:
                    st.error("Please enter at least one ZIP code for business searches.")
                else:
                    mode = "marketing" if search_mode == "Marketing Prospect Finder" else "custom"
                    progress = st.progress(0, text="Searching businesses...")

                    for idx, z in enumerate(zips):
                        rows = discover_businesses(
                            z,
                            float(radius),
                            mode,
                            category_or_topic.strip(),
                            use_google,
                            use_osm or not use_google,
                        )

                        for row in rows:
                            row["search_mode"] = search_mode
                            row["search_keyword"] = category_or_topic.strip()
                            row["source_zip"] = z
                            row["area_label"] = area_label.strip()

                        all_rows.extend(rows)
                        progress.progress(
                            (idx + 1) / len(zips),
                            text=f"Business search {idx + 1}/{len(zips)}",
                        )

                    progress.empty()

                    if do_enrich and all_rows:
                        limit = min(len(all_rows), int(enrich_limit))
                        if limit > 0:
                            st.info(f"Enriching {limit} rows.")
                            enriched = enrich_rows(all_rows[:limit])
                            all_rows = enriched + all_rows[limit:]

                    if do_score and all_rows:
                        all_rows = score_rows(all_rows)

            else:
                target_zips = zips if zips else [""]
                progress = st.progress(0, text="Searching public pages...")

                for idx, z in enumerate(target_zips):
                    rows = search_public_topics(
                        search_mode,
                        category_or_topic.strip(),
                        z,
                        area_label.strip(),
                        max_pages,
                        use_google,
                        public_pages_only,
                    )

                    for row in rows:
                        row["search_mode"] = search_mode
                        row["search_keyword"] = category_or_topic.strip()
                        row["source_zip"] = z
                        row["area_label"] = area_label.strip()

                    all_rows.extend(rows)
                    progress.progress(
                        (idx + 1) / len(target_zips),
                        text=f"Public search {idx + 1}/{len(target_zips)}",
                    )

                progress.empty()

            if not all_rows:
                st.warning("No results found.")
            else:
                df = pd.DataFrame(all_rows)
                df = dedupe_dataframe(df)
                df = sort_by_score_if_present(df)

                if trim_results:
                    df = df.head(int(final_cap)).copy()

                st.session_state.results_df = df
                st.session_state.last_run_meta = {
                    "search_mode": search_mode,
                    "keyword": category_or_topic.strip(),
                    "area_label": area_label.strip(),
                    "scan_mode": scan_mode,
                    "radius": radius,
                    "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                st.success(f"Found {len(df)} results.")
                render_results_card(df, title="Lead Results")

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                excel_bytes = get_excel_bytes(df)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        "Download Search Results CSV",
                        data=csv_bytes,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with d2:
                    st.download_button(
                        "Download Search Results Excel",
                        data=excel_bytes,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

        except Exception as e:
            st.error(f"Error: {e}")


# -------------------------------------------------
# TAB 2: CLIENT PACKAGE BUILDER
# -------------------------------------------------
with tab2:
    render_section_header(
        "Build a Client Package",
        "Turn current results into client-ready CSV, Excel, CRM, and ZIP exports.",
    )

    if st.session_state.results_df.empty:
        st.info("Run a search first in the Campaign Search tab.")
    else:
        df = sort_by_score_if_present(st.session_state.results_df.copy())
        meta = st.session_state.last_run_meta or {}

        c1, c2, c3 = st.columns(3)
        with c1:
            package_name = st.text_input("Package Name", value="Leavenworth Roofing Leads")
        with c2:
            prepared_by = st.text_input("Prepared By", value="Amanda")
        with c3:
            max_rows = st.number_input(
                "Max Leads in Package",
                min_value=10,
                max_value=5000,
                value=min(1000, len(df)),
                step=10,
            )

        package_df = df.head(int(max_rows)).copy()
        client_df = get_client_export_df(package_df)
        crm_df = get_crm_export_df(package_df)

        summary_text = build_summary_text(
            package_df,
            package_name=package_name,
            prepared_by=prepared_by,
            search_mode=meta.get("search_mode", ""),
            keyword=meta.get("keyword", ""),
            area_label=meta.get("area_label", ""),
        )

        manifest = build_manifest(
            package_name=package_name,
            prepared_by=prepared_by,
            row_count=len(package_df),
            meta=meta,
        )

        st.text_area("Package Summary", value=summary_text, height=220)
        render_results_card(package_df, title="Package Preview")

        client_csv = client_df.to_csv(index=False).encode("utf-8")
        crm_csv = crm_df.to_csv(index=False).encode("utf-8")
        client_excel = get_excel_bytes(client_df)
        zip_bytes = get_package_zip_bytes(client_df, crm_df, summary_text, manifest)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "Client CSV",
                data=client_csv,
                file_name=f"{package_name.lower().replace(' ', '_')}_client.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "CRM CSV",
                data=crm_csv,
                file_name=f"{package_name.lower().replace(' ', '_')}_crm.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d3:
            st.download_button(
                "Client Excel",
                data=client_excel,
                file_name=f"{package_name.lower().replace(' ', '_')}_client.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with d4:
            st.download_button(
                "Full ZIP Package",
                data=zip_bytes,
                file_name=f"{package_name.lower().replace(' ', '_')}_package.zip",
                mime="application/zip",
                use_container_width=True,
            )

        st.caption(
            "Google Sheets-ready path: download CSV and import into Sheets, or upload the Excel file to Drive and open in Sheets."
        )


# -------------------------------------------------
# TAB 3: EXPANSION PLANNER
# -------------------------------------------------
with tab3:
    render_section_header(
        "Expansion Planner",
        "Generate public-intent and market-interest phrases to expand discovery coverage.",
    )

    planner_mode = st.selectbox(
        "Planner Mode",
        [
            "Public Intent Search",
            "Relocation Interest Finder",
            "Community Interest Finder",
        ],
        index=0,
    )
    planner_topic = st.text_input("Main Keyword", value="need a roofer")
    planner_zip = st.text_input("ZIP", value="66048")
    planner_area = st.text_input("Area Label", value="Leavenworth")

    phrases = expand_topic_queries(
        planner_mode,
        planner_topic.strip(),
        planner_zip.strip(),
        planner_area.strip(),
    )

    render_section_header(
        "Suggested Search Phrases",
        "Use these to widen discovery without lowering relevance too aggressively.",
    )

    for phrase in phrases:
        st.code(phrase, language=None)


st.markdown("---")
st.caption("Use this tool for public business discovery, enrichment, scoring, and client-ready package delivery.")