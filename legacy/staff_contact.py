# staff_contact.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from extractors import (
    extract_contact_lines,
    extract_phone_numbers,
    extract_emails,
    extract_update_date_candidates,
)


def _uniq_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def analyze_staff_contacts(
    official_recruit_rows: list[dict],
    external_recruit_rows: list[dict],
    debug: bool = False,
) -> dict:
    """
    公式採用系 + 外部求人系（ハローワーク等）を比較
    """
    official_pages = []
    external_pages = []

    official_contact_lines = []
    official_phones = []
    official_emails = []

    external_contact_lines = []
    external_phones = []
    external_emails = []

    for row in official_recruit_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)

        lines = extract_contact_lines(text)
        phones = extract_phone_numbers(text)
        emails = extract_emails(text)
        dates = extract_update_date_candidates(text)

        official_pages.append({
            "url": url,
            "contact_lines": lines[:20],
            "phones": phones[:10],
            "emails": emails[:10],
            "update_dates": dates[:5],
        })

        official_contact_lines.extend(lines)
        official_phones.extend(phones)
        official_emails.extend(emails)

    for row in external_recruit_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)

        lines = extract_contact_lines(text)
        phones = extract_phone_numbers(text)
        emails = extract_emails(text)
        dates = extract_update_date_candidates(text)

        external_pages.append({
            "url": url,
            "contact_lines": lines[:20],
            "phones": phones[:10],
            "emails": emails[:10],
            "update_dates": dates[:5],
        })

        external_contact_lines.extend(lines)
        external_phones.extend(phones)
        external_emails.extend(emails)

    official_contact_lines = _uniq_keep_order(official_contact_lines)
    official_phones = _uniq_keep_order(official_phones)
    official_emails = _uniq_keep_order(official_emails)

    external_contact_lines = _uniq_keep_order(external_contact_lines)
    external_phones = _uniq_keep_order(external_phones)
    external_emails = _uniq_keep_order(external_emails)

    # 採用結果
    adopted_contact_lines = official_contact_lines if official_contact_lines else external_contact_lines
    adopted_phones = official_phones if official_phones else external_phones
    adopted_emails = official_emails if official_emails else external_emails

    if official_contact_lines or official_phones or official_emails:
        adopted_source = "official"
        consistency = "一致" if set(official_phones).intersection(set(external_phones)) or set(official_emails).intersection(set(external_emails)) else "公式優先"
    elif external_contact_lines or external_phones or external_emails:
        adopted_source = "external"
        consistency = "外部求人のみ"
    else:
        adopted_source = "none"
        consistency = "不明"

    return {
        "status": "ok" if (adopted_contact_lines or adopted_phones or adopted_emails) else "not_found",
        "adopted_source": adopted_source,
        "consistency": consistency,
        "official_contact_lines": official_contact_lines[:50],
        "official_phones": official_phones[:20],
        "official_emails": official_emails[:20],
        "external_contact_lines": external_contact_lines[:50],
        "external_phones": external_phones[:20],
        "external_emails": external_emails[:20],
        "adopted_contact_lines": adopted_contact_lines[:50],
        "adopted_phones": adopted_phones[:20],
        "adopted_emails": adopted_emails[:20],
        "debug_official_pages": official_pages if debug else [],
        "debug_external_pages": external_pages if debug else [],
    }
