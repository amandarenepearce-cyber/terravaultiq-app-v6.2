from __future__ import annotations

import pandas as pd


def score_rows(rows: list[dict]) -> list[dict]:
    scored = []
    for row in rows:
        item = dict(row)

        website_present = 10 if str(item.get("website", "")).strip() else 0
        email_present = 25 if str(item.get("primary_email", "")).strip() else 0
        phone_present = 15 if str(item.get("primary_phone", "")).strip() else 0
        socials_present = 10 if any(str(item.get(k, "")).strip() for k in ["facebook_link", "instagram_link", "linkedin_link"]) else 0

        bad_site = pd.to_numeric(pd.Series([item.get("bad_website_score", 0)]), errors="coerce").fillna(0).iloc[0]
        website_quality = max(0, 30 - int(bad_site / 4))

        ratings_total = pd.to_numeric(pd.Series([item.get("ratings_total", 0)]), errors="coerce").fillna(0).iloc[0]
        reviews_score = min(10, int(ratings_total / 10))

        item["business_fit_score"] = website_present + reviews_score
        item["digital_maturity_score"] = website_quality
        item["contactability_score"] = email_present + phone_present + socials_present
        item["website_quality_score"] = website_quality
        item["priority_score"] = 15 if str(item.get("priority", "")).lower() == "high" else 10 if str(item.get("priority", "")).lower() == "medium" else 5

        total = (
            item["business_fit_score"]
            + item["digital_maturity_score"]
            + item["contactability_score"]
            + item["priority_score"]
        )
        item["lead_score"] = min(100, total)

        if item["lead_score"] >= 80:
            item["lead_tier"] = "A"
        elif item["lead_score"] >= 60:
            item["lead_tier"] = "B"
        else:
            item["lead_tier"] = "C"
        scored.append(item)
    return scored
