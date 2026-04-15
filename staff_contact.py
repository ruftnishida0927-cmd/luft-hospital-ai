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
# Google検索（簡易）
# =========================
def search_urls(query):
    urls = []
    try:
        url = f"https://www.google.com/search?q={query}"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a"):
            href = a.get("href")
            if href and "http" in href and "google" not in href:
                urls.append(href)
            if len(urls) >= 5:
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

    # 電話番号
    tel = re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", html)
    if tel:
        data["代表電話"] = tel.group()

    # 看護部長
    nurse = extract_name(r"看護部長[:：]?\s*([一-龥ぁ-んァ-ン]+)", html)
    if nurse:
        data["看護部長"] = nurse

    # 事務長
    admin = extract_name(r"事務長[:：]?\s*([一-龥ぁ-んァ-ン]+)", html)
    if admin:
        data["事務長"] = admin

    return data


# =========================
# スコア計算
# =========================
def calculate_score(text, url):
    score = 0

    # ドメインスコア
    score += get_domain_score(url)

    # キーワードスコア
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

    # =========================
    # 検索クエリ（強化版）
    # =========================
    queries = [
        f"{hospital_name} {area} 看護部長",
        f"{hospital_name} {area} 事務長",
        f"{hospital_name} {area} 病院概要",
        f"{hospital_name} {area} 採用情報",
        f"{hospital_name} 看護部 PDF"
    ]

    urls = []
    for q in queries:
        urls.extend(search_urls(q))
        time.sleep(1)

    # 重複削除＆制限
    urls = list(set(urls))[:5]
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

            # 抽出できたら加点
            score += len(extracted) * 3

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
# 通常呼び出し
# =========================
def get_staff_contact(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    contact, _ = get_staff_contact_debug(hospital_name, area, hospital_info)
    return contact
