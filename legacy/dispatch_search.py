# -*- coding: utf-8 -*-
from extractors import build_job_features
from match_engine import build_match_result
from search_provider import search_web, fetch_page_text


def extract_local_context(text, keyword, window=400):
    """
    キーワード周辺だけ切り出す
    ページ混在対策
    """

    if not keyword:
        return text[:800]

    idx = text.find(keyword)

    if idx == -1:
        return text[:800]

    start = max(0, idx - window)
    end = idx + window

    return text[start:end]


def _is_likely_job_url(url: str) -> bool:
    u = url.lower()

    job_keywords = [
        "indeed",
        "townwork",
        "rikunabi",
        "job-medley",
        "staffservice",
        "manpower",
        "hatarako",
        "baitoru",
        "career",
        "mc-nurse",
        "en-gage",
        "求人"
    ]

    for kw in job_keywords:
        if kw in u:
            return True

    return False


def search_dispatch_jobs(hospital_info):

    name = hospital_info["病院名"]
    region = hospital_info.get("地域", "不明")
    station = hospital_info.get("最寄駅", "不明")

    queries = [
        f"{name} 看護助手 派遣",
        f"{name} 医療事務 派遣",
        f"{name} 看護補助 派遣",
        f"{name} 無資格 病院 派遣",
        f"{station} 看護助手 派遣",
        f"{station} 医療事務 派遣",
        f"{region} 看護助手 派遣 病院"
    ]

    candidate_urls = []

    for query in queries:

        results = search_web(query)

        for r in results:

            url = r["url"]

            if not _is_likely_job_url(url):
                continue

            candidate_urls.append(url)

    # 重複除去
    deduped_urls = []
    seen = set()

    for u in candidate_urls:
        if u in seen:
            continue
        seen.add(u)
        deduped_urls.append(u)

    results = []

    for url in deduped_urls[:5]:

        text = fetch_page_text(url)

        if not text:
            continue

        # ここが重要（病院名周辺のみ抽出）
        local = extract_local_context(
            text,
            hospital_info["病院名"]
        )

        job_features = build_job_features(local)

        match = build_match_result(
            hospital_info,
            job_features
        )

        results.append({
            "URL": url,
            "一致率": match["一致率"],
            "判定": match["判定"],
            "根拠": " / ".join(match["根拠"]),
            "最寄駅": job_features["最寄駅"],
            "徒歩": job_features["徒歩分数"],
            "地域": job_features["地域"],
            "職種": ",".join(job_features["職種キーワード"])
        })

    results.sort(
        key=lambda x: x["一致率"],
        reverse=True
    )

    return results[:5]
