# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import time

# =========================
# 設定
# =========================
HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = {
    "看護部長": 5,
    "事務長": 5,
    "採用担当": 4,
    "人事": 3,
    "TEL": 3,
    "電話": 3
}

NG_WORDS = ["blog", "note", "ameblo", "yahoo", "rakuten"]


# =========================
# ドメイン評価
# =========================
def get_domain_score(url):
    if "go.jp" in url:
        return 5
    if "ac.jp" in url:
        return 4
    if "hospital" in url or "hp." in url:
        return 3
    if "recruit" in url:
        return 2
    return 1


# =========================
# ノイズ除去
# =========================
def is_noise(url):
    return any(n in url for n in NG_WORDS)


# =========================
# Google検索（軽量版）
# =========================
def search_urls(query, max_results=5):
    urls = []
    try:
        url = f"https://www.google.com/search?q={query}"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a"):
            href = a.get("href")
            if href and "http" in href and "google" not in href:
                urls.append(href)
            if len(urls) >= max_results:
                break
    except:
        pass

    return urls


# =========================
# 名前抽出
# =========================
def extract_name(pattern, text):
    match = re.search(pattern, text)
    if match:
        name = match.group(1)
        if len(name) <= 10:
            return name
    return None


# =========================
# HTMLから情報抽出
# =========================
def extract_contact_from_html(html):
    data = {}

    tel = re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", html)
    if tel:
        data["代表電話"] = tel.group()

    nurse = extract_name(r"看護部長[:：]?\s*([一-龥ぁ-んァ-ン]+)", html)
    if nurse:
        data["看護部長"] = nurse

    admin = extract_name(r"事務長[:：]?\s*([一-龥ぁ-んァ-ン]+)", html)
    if admin:
        data["事務長"] = admin

    return data


# =========================
# スコア計算
# =========================
def calculate_score(text, url):
    score = 0
    score += get_domain_score(url)

    for k, v in KEYWORDS.items():
        if k in text:
            score += v

    return score


# =========================
# メイン（デバッグあり）
# =========================
def get_staff_contact_debug(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    contact = {
        "看護部長": "不明",
        "事務長": "不明",
        "人事担当": "不明",
        "代表電話": "不明",
        "採用窓口": "不明",
        "URL": "",
        "スコア": 0
    }

    debug = {
        "candidate_url_count": 0,
        "page_details": []
    }

    # 軽量化：クエリは4つに制限
    queries = [
        f"{hospital_name} {area} 看護部長",
        f"{hospital_name} {area} 事務長",
        f"{hospital_name} 病院概要",
        f"{hospital_name} 採用情報"
    ]

    urls = []
    for q in queries:
        urls.extend(search_urls(q, max_results=5))
        time.sleep(1)

    # 軽量化：最大8件まで
    urls = list(set(urls))[:8]
    debug["candidate_url_count"] = len(urls)

    best_score = 0

    for url in urls:
        try:
            if is_noise(url):
                continue

            res = requests.get(url, headers=HEADERS, timeout=5)
            html = res.text

            extracted = extract_contact_from_html(html)
            score = calculate_score(html, url)
            score += len(extracted) * 3

            # debugも制限
            if len(debug["page_details"]) < 5:
                debug["page_details"].append({
                    "url": url,
                    "score": score,
                    "data": extracted
                })

            if score > best_score:
                best_score = score
                contact.update(extracted)
                contact["URL"] = url
                contact["スコア"] = score

        except:
            continue

    return contact, debug


# =========================
# 通常呼び出し（DEBUG切替）
# =========================
def get_staff_contact(hospital_name: str, area: str = "", hospital_info: dict | None = None, debug_mode=False):
    if debug_mode:
        return get_staff_contact_debug(hospital_name, area, hospital_info)
    else:
        contact, _ = get_staff_contact_debug(hospital_name, area, hospital_info)
        return contact
