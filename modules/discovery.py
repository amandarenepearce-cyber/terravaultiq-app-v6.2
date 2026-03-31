from __future__ import annotations

from typing import List, Dict

import pandas as pd
import requests

HEADERS = {"User-Agent": "TerraVaultIQ/1.0"}

BUSINESS_QUERY_EXPANSIONS = {
    "roof": ["roofing", "roofing contractor", "roof repair", "roof replacement", "commercial roofing"],
    "clean": ["cleaning company", "house cleaning", "maid service", "deep cleaning service"],
    "med spa": ["med spa", "medical spa", "aesthetic clinic", "botox clinic"],
    "dent": ["dentist", "cosmetic dentist", "family dentist", "dental office"],
    "law": ["law firm", "personal injury lawyer", "criminal defense lawyer", "family law attorney"],
}


def expand_business_queries(keyword: str) -> List[str]:
    keyword = str(keyword).strip().lower()
    if not keyword:
        return []
    for trigger, options in BUSINESS_QUERY_EXPANSIONS.items():
        if trigger in keyword:
            return options
    return [keyword, f"{keyword} company", f"{keyword} service"]


def discover_businesses(
    zip_code: str,
    radius_miles: float,
    mode: str,
    keyword: str,
    use_google: bool,
    use_osm: bool,
    max_total: int = 1000,
) -> List[Dict]:
    rows: List[Dict] = []
    query_list = expand_business_queries(keyword)

    # The Google-enabled implementation is intentionally config-safe. If you add
    # a real API key flow, wire it here and preserve the same row schema.
    if use_osm:
        rows.extend(discover_businesses_osm(zip_code, query_list, max_total=max_total))

    deduped = dedupe_rows(rows)
    return deduped[:max_total]


def discover_businesses_osm(zip_code: str, queries: List[str], max_total: int = 1000) -> List[Dict]:
    # ZIP geocoding via Nominatim
    geo = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"postalcode": zip_code, "countrycodes": "us", "format": "jsonv2", "limit": 1},
        headers=HEADERS,
        timeout=30,
    )
    geo.raise_for_status()
    results = geo.json()
    if not results:
        return []
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])

    all_rows: List[Dict] = []
    for query in queries:
        if len(all_rows) >= max_total:
            break
        overpass = f"""
        [out:json][timeout:45];
        (
          node[\"name\"](around:25000,{lat},{lon});
          way[\"name\"](around:25000,{lat},{lon});
          relation[\"name\"](around:25000,{lat},{lon});
        );
        out center tags;
        """
        resp = requests.get(
            "https://overpass-api.de/api/interpreter",
            params={"data": overpass},
            headers=HEADERS,
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        for element in payload.get("elements", []):
            tags = element.get("tags", {})
            name = str(tags.get("name", "")).strip()
            if not name:
                continue
            haystack = " ".join([name.lower(), tags.get("shop", "").lower(), tags.get("craft", "").lower(), tags.get("office", "").lower(), tags.get("amenity", "").lower()])
            if query.lower().split()[0] not in haystack:
                continue
            website = tags.get("website", "") or tags.get("contact:website", "")
            phone = tags.get("phone", "") or tags.get("contact:phone", "")
            address = ", ".join([v for v in [tags.get("addr:housenumber", ""), tags.get("addr:street", ""), tags.get("addr:city", ""), tags.get("addr:state", ""), tags.get("addr:postcode", "")] if v])
            all_rows.append(
                {
                    "name": name,
                    "business_type": query,
                    "search_keyword": query,
                    "search_area": zip_code,
                    "address": address,
                    "website": website,
                    "phone": phone,
                    "rating": "",
                    "ratings_total": "",
                    "google_maps_url": "",
                    "place_id": "",
                    "types": ", ".join([v for v in [tags.get("shop", ""), tags.get("craft", ""), tags.get("office", ""), tags.get("amenity", "")] if v]),
                    "source_query": query,
                }
            )
            if len(all_rows) >= max_total:
                break
    return all_rows[:max_total]


def dedupe_rows(rows: List[Dict]) -> List[Dict]:
    seen = set()
    cleaned: List[Dict] = []
    for row in rows:
        key = (
            str(row.get("name", "")).strip().lower(),
            str(row.get("address", "")).strip().lower(),
            str(row.get("website", "")).strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(row)
    return cleaned


def expand_topic_queries(search_mode: str, topic: str, zip_code: str = "", area_label: str = "") -> List[str]:
    topic = topic.strip()
    where = area_label or zip_code
    suffix = f" in {where}" if where else ""
    if search_mode == "Public Intent Search":
        return [
            f"best {topic}{suffix}",
            f"recommend a {topic}{suffix}",
            f"looking for {topic}{suffix}",
            f"who knows a good {topic}{suffix}",
        ]
    if search_mode == "Relocation Interest Finder":
        return [
            f"moving to {topic}",
            f"living in {topic}",
            f"best neighborhoods in {topic}",
            f"relocating to {topic}",
        ]
    return [
        f"{topic} community{suffix}",
        f"{topic} group{suffix}",
        f"{topic} events{suffix}",
        f"{topic} clubs{suffix}",
    ]


def search_public_topics(search_mode: str, topic: str, zip_code: str, area_label: str, max_pages: int, use_google: bool, public_pages_only: bool) -> List[Dict]:
    rows = []
    for phrase in expand_topic_queries(search_mode, topic, zip_code=zip_code, area_label=area_label):
        rows.append(
            {
                "title": phrase,
                "snippet": "Suggested public search phrase",
                "source": "planner",
                "url": "",
                "source_query": phrase,
            }
        )
    return rows
