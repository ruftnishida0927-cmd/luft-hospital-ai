# source_hospital.py
# -*- coding: utf-8 -*-

import re
from urllib.parse import quote_plus

from search_provider import (
    fetch_page_html,
    extract_links,
    get_domain,
)


CATEGORY_KEYWORDS = {
    "basic": [
        "病院紹介", "病院概要", "当院について", "病院案内", "医院案内",
        "アクセス", "所在地", "外来案内", "診療案内", "入院案内",
    ],
    "facility": [
        "施設基準", "加算", "届出", "届け出", "診療報酬",
        "入院料", "入院基本料", "算定", "掲示事項",
    ],
    "recruit": [
        "採用", "求人", "募集", "リクルート", "採用情報",
        "求人情報", "看護師募集", "スタッフ募集", "エントリー",
    ],
    "group": [
        "グループ", "法人概要", "法人案内", "関連施設", "関連病院",
        "関連事業所", "施設一覧", "病院一覧", "事業所一覧", "法人情報",
    ],
    "contact": [
        "お問い合わせ", "問合せ", "お問合せ", "連絡先", "窓口", "担当",
    ],
}


def classify_source(url: str) -> str:
    domain = get_domain(url)

    if not domain:
        return "unknown"
    if any(x in domain for x in ["lg.jp", "pref.", "city.", "mhlw.go.jp"]):
        return "public"
    if any(x in domain for x in ["byoinnavi.jp", "caloo.jp", "qlife.jp", "medicalnote.jp", "fdoc.jp"]):
        return "medical-db"
    return "official"


def is_search_page_url(url: str) -> bool:
    if not url:
        return False
    patterns = [
        "freeword?q=",
        "/search/all",
        "search_hospital_result",
        "/search?",
        "/search/",
    ]
    return any(p in url for p in patterns)


def build_helper_links(hospital_name: str, prefecture: str = "") -> dict:
    q = quote_plus(f"{hospital_name} {prefecture}".strip())
    return {
        "google_search": f"https://www.google.com/search?q={q}",
        "byoinnavi_search": f"https://byoinnavi.jp/freeword?q={q}",
        "caloo_search": f"https://caloo.jp/search/all?s={q}",
        "qlife_search": f"https://www.qlife.jp/search_hospital_result?keyword={q}",
    }


def _category_score(text: str, url: str, category: str) -> int:
    score = 0
    text = f"{text} {url}"

    for kw in CATEGORY_KEYWORDS.get(category, []):
        if kw in text:
            score += 3

    return score


def discover_related_pages(main_url: str, extra_urls: list[str] | None = None, max_pages: int = 25) -> dict:
    """
    メインURLから同一ドメイン内リンクを収集して、
    basic / facility / recruit / group / contact に分類する
    """
    extra_urls = extra_urls or []

    html_text, err = fetch_page_html(main_url, timeout=15)
    if err:
        return {
            "status": "error",
            "error": err,
            "main_url": main_url,
            "all_links": [],
            "categories": {
                "basic": [],
                "facility": [],
                "recruit": [],
                "group": [],
                "contact": [],
            },
        }

    same_domain_links = extract_links(main_url, html_text, same_domain_only=True)

    all_candidates = []
    seen = set()

    # main_url 自体も候補に含める
    base_rows = [{
        "url": main_url,
        "text": "トップページ",
        "title": "",
    }] + same_domain_links

    for row in base_rows:
        url = row.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)

        if is_search_page_url(url):
            continue

        label = f"{row.get('text', '')} {row.get('title', '')}".strip()
        all_candidates.append({
            "url": url,
            "label": label,
            "basic_score": _category_score(label, url, "basic"),
            "facility_score": _category_score(label, url, "facility"),
            "recruit_score": _category_score(label, url, "recruit"),
            "group_score": _category_score(label, url, "group"),
            "contact_score": _category_score(label, url, "contact"),
        })

    for u in extra_urls:
        if not u or u in seen:
            continue
        if is_search_page_url(u):
            continue
        seen.add(u)
        all_candidates.append({
            "url": u,
            "label": "追加URL",
            "basic_score": 0,
            "facility_score": 0,
            "recruit_score": 10,
            "group_score": 0,
            "contact_score": 6,
        })

    categories = {}
    for cat in ["basic", "facility", "recruit", "group", "contact"]:
        key = f"{cat}_score"
        rows = sorted(all_candidates, key=lambda x: x[key], reverse=True)
        rows = [r for r in rows if r[key] > 0][:8]
        categories[cat] = rows

    return {
        "status": "ok",
        "error": "",
        "main_url": main_url,
        "all_links": all_candidates[:max_pages],
        "categories": categories,
    }
