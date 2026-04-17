# staff_contact.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from extractors import extract_contact_lines, extract_phone_numbers, extract_emails


def analyze_staff_contacts(url_rows: list[dict], debug: bool = False) -> dict:
    """
    recruit/contactカテゴリのURL群から、採用窓口候補を抽出
    人名断定ではなく、窓口候補・部署候補・連絡先候補を出す
    """
    page_results = []
    all_contact_lines = []
    all_phones = []
    all_emails = []

    for row in url_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=50000)

        contact_lines = extract_contact_lines(text)
        phones = extract_phone_numbers(text)
        emails = extract_emails(text)

        page_results.append({
            "url": url,
            "contact_line_count": len(contact_lines),
            "phones": phones[:10],
            "emails": emails[:10],
            "contact_lines": contact_lines[:20],
        })

        all_contact_lines.extend(contact_lines)
        all_phones.extend(phones)
        all_emails.extend(emails)

    def uniq_keep_order(items):
        seen = set()
        out = []
        for x in items:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    contact_lines = uniq_keep_order(all_contact_lines)[:50]
    phones = uniq_keep_order(all_phones)[:20]
    emails = uniq_keep_order(all_emails)[:20]

    status = "ok" if contact_lines or phones or emails else "not_found"

    return {
        "status": status,
        "contact_lines": contact_lines,
        "phones": phones,
        "emails": emails,
        "debug_pages": page_results if debug else [],
    }
