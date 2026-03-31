import io
from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st

from modules.discovery import discover_businesses, search_public_topics, expand_topic_queries
from modules.enrichment import enrich_rows
from modules.scoring import score_rows
from modules.ui_theme import inject_brand_theme
from modules import packager as packager_mod
from modules import exports as exports_mod


# -----------------------------
# App setup
# -----------------------------
st.set_page_config(
    page_title="TerraVaultIQ",
    page_icon="🧠",
    layout="wide",
)

inject_brand_theme()

if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if "last_run_meta" not in st.session_state:
    st.session_state.last_run_meta = {}


# -----------------------------
# Safe helper bindings / fallbacks
# -----------------------------
def _fallback_normalize_zip_list(text: str) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\n", ",").split(",")]
    return [p for p in parts if p]


normalize_zip_list = getattr(packager_mod, "normalize_zip_list", _fallback_normalize_zip_list)
build_client_export_df = getattr(packager_mod, "build_client_export_df", None)
build_crm_export_df = getattr(packager_mod, "build_crm_export_df", None)
build_package_zip_bytes = getattr(exports_mod, "build_package_zip_bytes", None)
dataframe_to_excel_bytes = getattr(exports_mod, "dataframe_to_excel_bytes", None)


# -----------------------------
# Helpers
# -----------------------------
def render_hero():
    st.markdown(
        """
        <div class="tv-hero">
            <div class="tv-pill">TerraVaultIQ • Lead Intelligence</div>
            <h1>
                Build launch-ready<br>
                <span class="accent">lead packages</span>
            </h1>
            <p>
                Discover, enrich, score, and package up to 1,000 leads with premium exports
                built for internal teams, outreach workflows, Excel delivery, and Google Sheets-ready handoff.
            </p>
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
    ).drop(columns=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"])

    return work.reset_index(drop=True)


def sort_by_score_if_present(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "lead_score" not in df.columns:
        return df.reset_index(drop=True)

    work = df.copy()
    work["_lead_score_num"] = pd.to_numeric(work["lead_score"], errors="coerce").fillna(-1)
    work = work.sort_values("_lead_score_num", ascending=False).drop(columns=["_lead_score_num"])
    return work.reset_index(drop=True)


def safe_metric_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].astype(str).str.strip().replace("nan", "").ne("").sum())


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
):
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
    out["primary_phone"] = df["primary_phone"] if "primary_phone" in df.columns else (df["phone"] if "phone" in df.columns else "")
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


def build_package_zip_fallback(
    client_df: pd.DataFrame,
    crm_df: pd.DataFrame,
    summary_text: str,
    manifest: dict,
) -> bytes:
    import json
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
    st.markdown(f'<div class="tv-card"><h2>{title}</h2>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Results", len(df))
    m2.metric("With Website", safe_metric_count(df, "website"))
    m3.metric("With Email", safe_metric_count(df, "primary_email"))
    m4.metric("High Score", high_score_count(df))

    st.dataframe(df, use_container_width=True, hide_index=True, height=520)
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Hero
# -----------------------------
render_hero()

tab1, tab2, tab3 = st.tabs(
    ["Campaign Search", "Client Package Builder", "Expansion Planner"]
)


# -----------------------------
# TAB 1: SEARCH
# -----------------------------
with tab1:
    left_col, right_col = st.columns([2.1, 1], gap="large")

    with left_col:
        st.markdown('<div class="tv-card"><h2>Location & Keywords</h2>', unsafe_allow_html=True)

        scan_mode = st.radio(
            "Scan Mode",
            ["Single ZIP Deep Scan", "Multi-ZIP Area Scan"],
            index=1,
            horizontal=True,
            key="scan_mode_main_left",
        )

        if scan_mode == "Single ZIP Deep Scan":
            zip_code = st.text_input("ZIP CODE", value="60614")
            zip_list_text = ""
        else:
            zip_code = ""
            zip_list_text = st.text_area("ZIP LIST", value="60614, 60610, 60657, 60618", height=140)

        radius = st.number_input("RADIUS (miles)", min_value=1, max_value=100, value=25, step=1)
        area_label = st.text_input("CITY / AREA LABEL", value="Chicago IL")

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

        if search_mode in ["Public Intent Search", "Relocation Interest Finder", "Community Interest Finder"]:
            with st.expander("Suggested public search phrases"):
                for phrase in expand_topic_queries(
                    search_mode,
                    category_or_topic.strip(),
                    zip_code=zip_code.strip(),
                    area_label=area_label.strip(),
                ):
                    st.code(phrase, language=None)

        run_search = st.button("FIND LEADS", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="tv-card"><h2>Search Options</h2>', unsafe_allow_html=True)

        use_google = st.checkbox("Use Google API if available", value=True)
        use_osm = st.checkbox("Use OpenStreetMap backup", value=True)
        do_enrich = st.checkbox("Find public business contact info", value=True)
        enrich_limit = st.number_input("Max rows to enrich", min_value=0, max_value=5000, value=1000, step=50)
        do_score = st.checkbox("Score business leads", value=True)
        trim_results = st.checkbox("Trim final results", value=True)
        final_cap = st.selectbox("Final result cap", [100, 250, 500, 1000], index=3)

        public_pages_only = st.checkbox("Public pages only", value=True)
        max_pages = st.slider("Public search pages", 1, 5, 2)

        st.markdown("</div>", unsafe_allow_html=True)

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
                    prog = st.progress(0, text="Searching businesses...")

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
                        prog.progress((idx + 1) / len(zips), text=f"Business search {idx + 1}/{len(zips)}")

                    prog.empty()

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
                prog = st.progress(0, text="Searching public pages...")

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
                    prog.progress((idx + 1) / len(target_zips), text=f"Public search {idx + 1}/{len(target_zips)}")

                prog.empty()

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


# -----------------------------
# TAB 2: PACKAGE BUILDER
# -----------------------------
with tab2:
    st.markdown('<div class="tv-card"><h2>Build a Client Package</h2>', unsafe_allow_html=True)

    if st.session_state.results_df.empty:
        st.info("Run a search first in the Campaign Search tab.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        df = sort_by_score_if_present(st.session_state.results_df.copy())
        meta = st.session_state.last_run_meta or {}

        c1, c2, c3 = st.columns(3)
        with c1:
            package_name = st.text_input("Package Name", value="Chicago Roofing Leads")
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

        manifest = {
            "package_name": package_name,
            "prepared_by": prepared_by,
            "generated_at": datetime.now().isoformat(),
            "total_rows": int(len(package_df)),
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

        st.caption("Google Sheets-ready path: download CSV and import into Sheets, or upload the Excel file to Drive and open in Sheets.")
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# TAB 3: EXPANSION PLANNER
# -----------------------------
with tab3:
    st.markdown('<div class="tv-card"><h2>Expansion Planner</h2>', unsafe_allow_html=True)

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
    planner_zip = st.text_input("ZIP", value="60614")
    planner_area = st.text_input("Area Label", value="Chicago IL")

    phrases = expand_topic_queries(
        planner_mode,
        planner_topic.strip(),
        planner_zip.strip(),
        planner_area.strip(),
    )

    st.markdown('<div class="tv-card"><h2>Suggested Search Phrases</h2>', unsafe_allow_html=True)
    for phrase in phrases:
        st.code(phrase, language=None)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("---")
st.caption("Use this tool for public business discovery, enrichment, scoring, and client-ready package delivery.")