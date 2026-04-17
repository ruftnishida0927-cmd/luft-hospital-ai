# extractors.py
# -*- coding: utf-8 -*-

import re


PREFECTURES = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県",
]

DEPARTMENT_KEYWORDS = [
    "内科", "外科", "整形外科", "精神科", "心療内科", "小児科", "皮膚科",
    "泌尿器科", "産婦人科", "婦人科", "脳神経外科", "脳神経内科", "眼科",
    "耳鼻咽喉科", "形成外科", "放射線科", "麻酔科", "リハビリテーション科",
    "呼吸器内科", "消化器内科", "循環器内科", "糖尿病内科", "腎臓内科",
    "救急科", "病理診断科",
]

FUNCTION_KEYWORDS = [
    "急性期", "回復期", "慢性期", "療養", "救急", "二次救急", "三次救急",
    "地域包括ケア", "回復期リハビリテーション", "緩和ケア", "精神科", "認知症",
    "在宅医療", "訪問看護", "透析", "健診", "人間ドック",
]

FACILITY_KEYWORDS = [
    "施設基準", "届出", "届け出", "加算", "入院料", "入院基本料",
    "特定入院料", "診療報酬", "算定", "掲示事項",
]

CONTACT_TITLE_KEYWORDS = [
    "採用担当", "人事", "総務", "事務長", "看護部長", "看護部", "採用窓口",
    "担当者", "担当", "お問い合わせ", "連絡先",
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str):
    return [line.strip() for line in clean_text(text).split("\n") if line.strip()]


def extract_prefecture(text: str) -> str:
    for p in PREFECTURES:
        if p in text:
            return p
    return "不明"


def _contains_address_shape(text: str) -> bool:
    return re.search(r"(北海道|..県|..府|東京都).{0,40}(市|区|町|村)", text) is not None


def _normalize_address_candidate(text: str) -> str:
    text = text.strip(" ：:・-")
    text = re.sub(r"(TEL|電話|FAX|アクセス|診療科|診療時間|休診日|地図|MAP).*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_address(text: str) -> str:
    candidates = []

    for line in split_lines(text):
        if not _contains_address_shape(line):
            continue

        score = 0
        if "所在地" in line:
            score += 10
        if "住所" in line:
            score += 10
        if "アクセス" in line:
            score += 2

        m = re.search(r"((北海道|..県|..府|東京都).{0,70}?(市|区|町|村).{0,50})", line)
        if m:
            candidates.append((score, _normalize_address_candidate(m.group(1))))

    for pat in [
        r"(所在地|住所)[:：]?\s*((北海道|..県|..府|東京都).{0,70}?(市|区|町|村).{0,50})",
        r"(アクセス)[:：]?\s*((北海道|..県|..府|東京都).{0,70}?(市|区|町|村).{0,50})",
    ]:
        for m in re.finditer(pat, text):
            label = m.group(1)
            addr = _normalize_address_candidate(m.group(2))
            score = 12 if label in ["所在地", "住所"] else 4
            candidates.append((score, addr))

    if not candidates:
        return "不明"

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def extract_region(address: str) -> str:
    if not address or address == "不明":
        return "不明"

    m = re.search(r"(北海道|..県|..府|東京都)(.{1,12}?(市|区|町|村))", address)
    if m:
        return f"{m.group(1)}{m.group(2)}"

    pref = extract_prefecture(address)
    return pref if pref != "不明" else "不明"


def extract_nearest_station(text: str) -> str:
    for line in split_lines(text):
        for pat in [
            r"([^\s　]{1,20}駅)\s*(より)?\s*(徒歩|バス|車)\s*\d{1,2}分",
            r"最寄り駅[:：]?\s*([^\s　]{1,20}駅)",
            r"アクセス[:：]?\s*([^\s　]{1,20}駅)",
        ]:
            m = re.search(pat, line)
            if m:
                for g in m.groups():
                    if g and "駅" in g:
                        return g.strip()
    return "不明"


def extract_bed_count(text: str) -> str:
    for line in split_lines(text):
        for pat in [
            r"病床数[:：]?\s*(\d{1,4})\s*床",
            r"許可病床数[:：]?\s*(\d{1,4})\s*床",
            r"(\d{1,4})\s*床",
        ]:
            m = re.search(pat, line)
            if m:
                return f"{m.group(1)}床"
    return "不明"


def extract_departments(text: str) -> str:
    found = []
    src = clean_text(text)
    for dep in DEPARTMENT_KEYWORDS:
        if dep in src and dep not in found:
            found.append(dep)
    return "、".join(found[:15]) if found else "不明"


def extract_hospital_type(text: str, title: str = "") -> str:
    src = f"{title}\n{text}"
    for t in [
        "精神科病院",
        "療養型病院",
        "ケアミックス病院",
        "一般病院",
        "大学病院",
        "総合病院",
        "リハビリテーション病院",
        "回復期リハビリテーション病院",
    ]:
        if t in src:
            return t
    return "不明"


def extract_function_hints(text: str) -> list[str]:
    found = []
    src = clean_text(text)
    for kw in FUNCTION_KEYWORDS:
        if kw in src and kw not in found:
            found.append(kw)
    return found


def extract_facility_lines(text: str) -> list[str]:
    rows = []
    for line in split_lines(text):
        if any(kw in line for kw in FACILITY_KEYWORDS):
            rows.append(line)
            continue
        if re.search(r"(入院料|入院基本料|加算|届出|施設基準)", line):
            rows.append(line)

    uniq = []
    seen = set()
    for row in rows:
        r = row.strip()
        if r and r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq[:80]


def split_facility_items(lines: list[str]) -> dict:
    basic_rates = []
    additions = []
    other_items = []

    for line in lines:
        if re.search(r"(入院料|入院基本料|特定入院料)", line):
            basic_rates.append(line)
        elif "加算" in line:
            additions.append(line)
        else:
            other_items.append(line)

    return {
        "basic_rates": basic_rates[:40],
        "additions": additions[:40],
        "other_items": other_items[:40],
    }


def extract_group_candidates(text: str) -> list[str]:
    lines = split_lines(text)
    rows = []

    for line in lines:
        if any(kw in line for kw in ["グループ", "関連施設", "関連病院", "法人", "施設一覧", "病院一覧"]):
            rows.append(line)

    uniq = []
    seen = set()
    for row in rows:
        if row not in seen:
            seen.add(row)
            uniq.append(row)

    return uniq[:40]


def extract_phone_numbers(text: str) -> list[str]:
    nums = re.findall(r"\b0\d{1,4}-\d{1,4}-\d{4}\b", text)
    uniq = []
    seen = set()
    for n in nums:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq[:20]


def extract_emails(text: str) -> list[str]:
    mails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    uniq = []
    seen = set()
    for m in mails:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq[:20]


def extract_contact_lines(text: str) -> list[str]:
    rows = []
    for line in split_lines(text):
        if any(kw in line for kw in CONTACT_TITLE_KEYWORDS):
            rows.append(line)

    uniq = []
    seen = set()
    for row in rows:
        if row not in seen:
            seen.add(row)
            uniq.append(row)

    return uniq[:40]


def extract_basic_facts(text: str, title: str = "", url: str = "") -> dict:
    address = extract_address(text)
    return {
        "address": address,
        "region": extract_region(address),
        "nearest_station": extract_nearest_station(text),
        "bed_count": extract_bed_count(text),
        "departments": extract_departments(text),
        "hospital_type": extract_hospital_type(text, title=title),
        "function_hints": extract_function_hints(text),
    }
