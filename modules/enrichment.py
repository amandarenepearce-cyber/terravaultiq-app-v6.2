from __future__ import annotations

import re
from urllib.parse import urljoin

import requests

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(\+?1?[\s\-.]?)?(\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
META_DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
HEADERS = {"User-Agent": "TerraVaultIQ/1.0"}


def normalize_website(website: str) -> str:
    website = str(website).strip()
    if not website:
        return ""
    if not website.startswith("http://") and not website.startswith("https://"):
        website = "https://" + website
    return website


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", str(text)).replace("\n", " ").replace("\r", " ").strip()


def website_audit(website: str) -> dict:
    website = normalize_website(website)
    empty = {
        "site_live": "no_website",
        "final_url": "",
        "emails_found": "",
        "phones_found": "",
        "facebook_link": "",
        "instagram_link": "",
        "linkedin_link": "",
        "title": "",
        "meta_description": "",
        "h1": "",
        "bad_website_score": 100,
        "website_notes": "No website found",
        "offer_angle": "Website build or landing page angle",
        "website_status": "missing_website",
    }
    if not website:
        return empty

    pages = [website, urljoin(website, "/contact"), urljoin(website, "/about"), urljoin(website, "/services")]
    emails = set()
    phones = set()
    facebook = ""
    instagram = ""
    linkedin = ""
    title = ""
    meta_desc = ""
    h1 = ""
    site_live = "no"
    final_url = website
    notes = []
    score = 0

    for i, page in enumerate(pages):
        try:
            response = requests.get(page, headers=HEADERS, timeout=15, allow_redirects=True)
            if i == 0:
                final_url = response.url
            if response.ok:
                site_live = "yes"
                text = response.text[:250000]
                for email in EMAIL_RE.findall(text):
                    lowered = email.lower()
                    if not lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
                        emails.add(email)
                for phone_match in PHONE_RE.findall(text):
                    phones.add("".join(phone_match).strip())
                if not facebook:
                    match = re.search(r'https?://[^\s"\'<>]*facebook\.com/[^\s"\'<>]+', text, re.I)
                    if match:
                        facebook = match.group(0)
                if not instagram:
                    match = re.search(r'https?://[^\s"\'<>]*instagram\.com/[^\s"\'<>]+', text, re.I)
                    if match:
                        instagram = match.group(0)
                if not linkedin:
                    match = re.search(r'https?://[^\s"\'<>]*linkedin\.com/[^\s"\'<>]+', text, re.I)
                    if match:
                        linkedin = match.group(0)
                if not title:
                    match = TITLE_RE.search(text)
                    if match:
                        title = strip_tags(match.group(1))[:140]
                if not meta_desc:
                    match = META_DESC_RE.search(text)
                    if match:
                        meta_desc = strip_tags(match.group(1))[:220]
                if not h1:
                    match = H1_RE.search(text)
                    if match:
                        h1 = strip_tags(match.group(1))[:160]
        except Exception:
            pass

    if site_live != "yes":
        score += 45
        notes.append("Website did not load cleanly")
    if final_url and not str(final_url).startswith("https://"):
        score += 10
        notes.append("Website is not on HTTPS")
    if not title:
        score += 10
        notes.append("Missing page title")
    if not meta_desc:
        score += 15
        notes.append("Missing meta description")
    if not h1:
        score += 8
        notes.append("Missing H1 heading")
    if not emails:
        score += 5
    if not phones:
        score += 5
    if not facebook and not instagram and not linkedin:
        score += 5
        notes.append("No social links found")

    score = max(0, min(score, 100))
    if score >= 70:
        offer = "Strong website rebuild angle"
    elif score >= 40:
        offer = "Website tune-up or lead page angle"
    else:
        offer = "SEO, ads, or conversion angle"

    return {
        "site_live": site_live,
        "final_url": final_url,
        "emails_found": ", ".join(sorted(emails)[:5]),
        "phones_found": ", ".join(sorted(phones)[:5]),
        "facebook_link": facebook,
        "instagram_link": instagram,
        "linkedin_link": linkedin,
        "title": title,
        "meta_description": meta_desc,
        "h1": h1,
        "bad_website_score": score,
        "website_notes": " | ".join(notes) if notes else "Website looks usable",
        "offer_angle": offer,
        "website_status": "has_website",
    }


def infer_contact_confidence(row: dict) -> str:
    score = 0
    if row.get("primary_email"):
        score += 2
    if row.get("primary_phone"):
        score += 1
    if row.get("website") or row.get("final_url"):
        score += 1
    if row.get("facebook_link") or row.get("instagram_link") or row.get("linkedin_link"):
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def enrich_rows(rows: list[dict]) -> list[dict]:
    enriched = []
    for row in rows:
        item = dict(row)
        website = item.get("website", "") or item.get("final_url", "")
        audit = website_audit(website)
        item.update(audit)

        emails = [e.strip() for e in str(audit.get("emails_found", "")).split(",") if e.strip()]
        phones = [p.strip() for p in str(audit.get("phones_found", "")).split(",") if p.strip()]
        item["primary_email"] = emails[0] if emails else ""
        item["secondary_email"] = emails[1] if len(emails) > 1 else ""
        item["primary_phone"] = phones[0] if phones else item.get("phone", "")
        item["contact_confidence"] = infer_contact_confidence(item)
        enriched.append(item)
    return enriched
