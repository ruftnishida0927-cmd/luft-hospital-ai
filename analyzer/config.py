USER_AGENT = (
    "Mozilla/5.0 (compatible; LuftHospitalAI/2.0; +https://render.com) "
    "Python requests"
)

TIMEOUT = 15
MAX_PAGES = 30
MAX_EXTERNAL_PAGES = 12
MAX_TEXT_CHARS = 35000
MAX_LINKS_PER_PAGE = 80

CATEGORY_HINTS = {
    "basic": [
        "病院概要", "医院概要", "当院について", "病院紹介", "診療案内", "外来案内", "入院案内", "アクセス", "概要", "案内",
        "about", "guide", "outline", "hospital", "access", "department",
    ],
    "facility": [
        "施設基準", "届出", "加算", "入院基本料", "看護配置", "厚生局", "基本料", "算定", "medical-fee", "standard",
    ],
    "recruit": [
        "採用", "求人", "募集", "看護師募集", "採用情報", "job", "recruit", "career", "employment",
    ],
    "group": [
        "法人概要", "法人案内", "関連施設", "グループ", "network", "group", "corporate", "法人", "施設一覧",
    ],
    "contact": [
        "お問い合わせ", "連絡先", "contact", "電話", "mail", "メール", "相談窓口",
    ],
    "public": [
        "厚生局", "保険医療機関", "医療情報ネット", "ナビイ", "wam", "自治体", "都道府県", "mhlw", "pref", "go.jp",
    ],
}

PUBLIC_DOMAIN_KEYWORDS = [
    "go.jp", "lg.jp", "pref.", "city.", "byouin", "iryo", "medical", "mhlw",
]

RECRUIT_DOMAIN_KEYWORDS = [
    "hellowork", "hello-work", "engage", "en-gage", "indeed", "mynavi", "rikunabi", "job", "career", "townwork",
]

GROUP_DOMAIN_KEYWORDS = [
    "group", "corporate", "medical", "kai", "or.jp", "gr.jp",
]

KNOWN_PATH_SEEDS = [
    "/about", "/guide", "/hospital", "/outline", "/access", "/department", "/contact",
    "/recruit", "/recruit/", "/career", "/jobs", "/group", "/corporate", "/facility-standards",
    "/standard", "/information", "/overview", "/privacy", "/sitemap.xml", "/robots.txt",
]

BASIC_FIELD_NAMES = [
    "住所", "地域", "最寄駅", "病床数", "診療科", "病院種別", "病院機能", "法人名", "代表電話", "メール",
]
