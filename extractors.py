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

ADDRESS_NOISE_WORDS = [
    "口コミ",
    "評判",
    "近くの病院",
    "周辺",
    "一覧",
    "ランキング",
    "地図を見る",
    "他の医療機関",
    "近隣",
    "広告",
    "スポンサー",
    "路線",
    "駅一覧",
    "診療時間",
    "予約",
    "QLife",
    "病院なび",
    "Caloo",
]

GENERIC_AMBIGUOUS_NAME_WORDS = [
    "中央病院",
    "市民病院",
    "総合病院",
    "記念病院",
    "徳洲会病院",
    "済生会病院",
    "赤十字病院",
    "厚生病院",
    "第一病院",
    "第二病院",
    "高雄病院",
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str):
    text = clean_text(text)
    return [line.strip() for line in text.split("\n") if line.strip()]


def extract_prefecture(text: str) -> str:
    if not text:
        return "不明"
    for p in PREFECTURES:
        if p in text:
            return p
    return "不明"


def _contains_full_address_shape(text: str) -> bool:
    if not text:
        return False
    return re.search(r"(北海道|..県|..府|東京都).{0,40}(市|区|町|村)", text) is not None


def _normalize_address_candidate(text: str) -> str:
    text = text.strip(" ：:・-")
    text = re.sub(r"(TEL|電話|FAX|アクセス|診療科|診療時間|休診日|地図|MAP).*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _address_candidate_score(line: str) -> int:
    score = 0

    if not line:
        return -999

    if any(noise in line for noise in ADDRESS_NOISE_WORDS):
        score -= 10

    if "所在地" in line:
        score += 8
    if "住所" in line:
        score += 8
    if "アクセス" in line:
        score += 2

    if _contains_full_address_shape(line):
        score += 6

    if len(line) > 100:
        score -= 3

    return score


def extract_address(text: str) -> str:
    lines = split_lines(text)

    candidates = []

    # 1) 行ベースで強く拾う
    for line in lines:
        if not _contains_full_address_shape(line):
            continue

        normalized = _normalize_address_candidate(line)
        score = _address_candidate_score(normalized)

        m = re.search(r"((北海道|..県|..府|東京都).{0,60}?(市|区|町|村).{0,40})", normalized)
        if m:
            addr = _normalize_address_candidate(m.group(1))
            candidates.append((score, addr))

    # 2) 所在地/住所ラベルの近辺を拾う
    patterns = [
        r"(所在地|住所)[:：]?\s*((北海道|..県|..府|東京都).{0,60}?(市|区|町|村).{0,40})",
        r"(アクセス)[:：]?\s*((北海道|..県|..府|東京都).{0,60}?(市|区|町|村).{0,40})",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            addr = _normalize_address_candidate(m.group(2))
            score = 12 if m.group(1) in ["所在地", "住所"] else 5
            if any(noise in addr for noise in ADDRESS_NOISE_WORDS):
                score -= 10
            candidates.append((score, addr))

    if not candidates:
        return "不明"

    # スコア優先、同点なら短すぎず長すぎないもの
    candidates = sorted(
        candidates,
        key=lambda x: (x[0], -abs(len(x[1]) - 25)),
        reverse=True
    )

    best = candidates[0][1]
    return best if best else "不明"


def extract_region(address: str) -> str:
    if not address or address == "不明":
        return "不明"

    m = re.search(r"(北海道|..県|..府|東京都)(.{1,12}?(市|区|町|村))", address)
    if m:
        return f"{m.group(1)}{m.group(2)}".strip()

    pref = extract_prefecture(address)
    if pref != "不明":
        return pref

    return "不明"


def extract_nearest_station(text: str) -> str:
    lines = split_lines(text)

    patterns = [
        r"([^\s　]{1,20}駅)\s*(より)?\s*(徒歩|バス|車)\s*\d{1,2}分",
        r"最寄り駅[:：]?\s*([^\s　]{1,20}駅)",
        r"アクセス[:：]?\s*([^\s　]{1,20}駅)",
    ]

    for line in lines:
        for pat in patterns:
            m = re.search(pat, line)
            if m:
                for g in m.groups():
                    if g and "駅" in g:
                        return g.strip()

    return "不明"


def extract_bed_count(text: str) -> str:
    lines = split_lines(text)

    patterns = [
        r"病床数[:：]?\s*(\d{1,4})\s*床",
        r"許可病床数[:：]?\s*(\d{1,4})\s*床",
        r"(\d{1,4})\s*床",
    ]

    for line in lines:
        for pat in patterns:
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

    return "、".join(found[:12]) if found else "不明"


def extract_hospital_type(text: str, title: str = "") -> str:
    src = f"{title}\n{text}"

    explicit_types = [
        "精神科病院",
        "療養型病院",
        "ケアミックス病院",
        "一般病院",
        "大学病院",
        "総合病院",
        "リハビリテーション病院",
    ]

    for t in explicit_types:
        if t in src:
            return t

    return "不明"


def extract_hospital_name_from_title(title: str) -> str:
    if not title:
        return "不明"

    title = clean_text(title)
    title = re.sub(r"\s*[\-|｜|].*$", "", title).strip()

    if "病院" in title:
        return title

    return "不明"


def is_generic_ambiguous_hospital_name(hospital_name: str) -> bool:
    if not hospital_name:
        return False

    normalized = re.sub(r"\s+", "", hospital_name)

    if normalized in GENERIC_AMBIGUOUS_NAME_WORDS:
        return True

    # 病院名が極端に短く、法人名も地名もない場合は曖昧扱い寄り
    if len(normalized) <= 5 and normalized.endswith("病院"):
        return True

    return False


def extract_basic_facts(text: str, title: str = "", url: str = "") -> dict:
    address = extract_address(text)
    region = extract_region(address)
    station = extract_nearest_station(text)
    bed_count = extract_bed_count(text)
    departments = extract_departments(text)
    hospital_type = extract_hospital_type(text, title=title)
    name_from_title = extract_hospital_name_from_title(title)

    return {
        "name_candidate": name_from_title,
        "address": address,
        "region": region,
        "nearest_station": station,
        "bed_count": bed_count,
        "departments": departments,
        "hospital_type": hospital_type,
    }
