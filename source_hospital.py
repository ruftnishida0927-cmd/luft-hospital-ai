# source_hospital.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_html, extract_links, get_domain


CATEGORY_KEYWORDS = {
    "basic": [
        "病院紹介", "病院概要", "当院について", "病院案内", "医院案内",
        "アクセス", "所在地", "外来案内", "診療案内", "入院案内",
        "診療科", "部門案内", "病床",
    ],
    "facility": [
        "施設基準", "加算", "届出", "届け出", "診療報酬",
        "入院料", "入院基本料", "算定", "掲示事項",
    ],
    "recruit": [
        "採用", "求人", "募集", "リクルート", "採用情報",
        "求人情報", "看護師募集", "スタッフ募集", "エントリー",
        "ハローワーク",
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
    from urllib.parse import quote_plus

    q = quote_plus(f"{hospital_name} {prefecture}".strip())
    return {
        "google_search": f"https://www.google.com/search?q={q}",
        "byoinnavi_search": f"https://byoinnavi.jp/freeword?q={q}",
        "caloo_search": f"https://caloo.jp/search/all?s={q}",
        "qlife_search": f"https://www.qlife.jp/search_hospital_result?keyword={q}",
    }


def parse_multiline_urls(raw_text: str) -> list[str]:
    rows = []
    seen = set()

    for line in raw_text.splitlines():
        u = line.strip()
        if not u:
            continue
        if u in seen:
            continue
        seen.add(u)
        rows.append(u)

    return rows


def _category_score(text: str, url: str, category: str) -> int:
    score = 0
    haystack = f"{text} {url}"

    for kw in CATEGORY_KEYWORDS.get(category, []):
        if kw in haystack:
            score += 3

    return score


def _to_scored_link_rows(source_url: str, links: list[dict]) -> list[dict]:
    rows = []

    for link in links:
        url = link.get("url", "")
        if not url or is_search_page_url(url):
            continue

        label = f"{link.get('text', '')} {link.get('title', '')}".strip()

        rows.append({
            "url": url,
            "label": label,
            "source_url": source_url,
            "source_type": classify_source(url),
            "basic_score": _category_score(label, url, "basic"),
            "facility_score": _category_score(label, url, "facility"),
            "recruit_score": _category_score(label, url, "recruit"),
            "group_score": _category_score(label, url, "group"),
            "contact_score": _category_score(label, url, "contact"),
        })

    return rows


def discover_related_pages(
    main_url: str,
    public_urls: list[str] | None = None,
    recruit_urls: list[str] | None = None,
    group_urls: list[str] | None = None,
    extra_official_urls: list[str] | None = None,
    max_pages: int = 40,
) -> dict:
    public_urls = public_urls or []
    recruit_urls = recruit_urls or []
    group_urls = group_urls or []
    extra_official_urls = extra_official_urls or []

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
                "public": [],
            },
        }

    same_domain_links = extract_links(main_url, html_text, same_domain_only=True)

    all_candidates = []
    seen = set()

    def push_manual_url(url: str, label: str, source_type: str):
        if not url or url in seen or is_search_page_url(url):
            return
        seen.add(url)
        all_candidates.append({
            "url": url,
            "label": label,
            "source_url": url,
            "source_type": source_type,
            "basic_score": 6 if "basic" in label else 0,
            "facility_score": 6 if "facility" in label else 0,
            "recruit_score": 6 if "recruit" in label else 0,
            "group_score": 6 if "group" in label else 0,
            "contact_score": 6 if "contact" in label else 0,
        })

    push_manual_url(main_url, "main basic", "official")

    for row in _to_scored_link_rows(main_url, same_domain_links):
        if row["url"] in seen:
            continue
        seen.add(row["url"])
        all_candidates.append(row)

    for u in extra_official_urls:
        push_manual_url(u, "basic official extra", "official")

    for u in public_urls:
        push_manual_url(u, "facility public source", "public")

    for u in recruit_urls:
        push_manual_url(u, "recruit contact", "recruit")

    for u in group_urls:
        push_manual_url(u, "group basic", "group")

    categories = {}

    for cat in ["basic", "facility", "recruit", "group", "contact"]:
        key = f"{cat}_score"
        rows = sorted(all_candidates, key=lambda x: (x[key], 1 if x["source_type"] == "public" else 0), reverse=True)
        rows = [r for r in rows if r[key] > 0][:10]
        categories[cat] = rows

    categories["public"] = [r for r in all_candidates if r["source_type"] == "public"][:10]

    return {
        "status": "ok",
        "error": "",
        "main_url": main_url,
        "all_links": all_candidates[:max_pages],
        "categories": categories,
    }
