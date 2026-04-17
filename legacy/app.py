# app.py
# -*- coding: utf-8 -*-

import streamlit as st

from hospital_basic import analyze_hospital_from_url
from source_hospital import build_helper_links, parse_multiline_urls


PREFECTURES = [
    "",
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

st.set_page_config(
    page_title="ルフト病院分析AI",
    page_icon="🏥",
    layout="wide",
)

st.title("ルフト病院分析AI")
st.error("BUILD MARKER: 2026-04-17 16:20")
st.caption("無料前提のURL解析版 / 複数ソース比較仕様")

st.sidebar.header("設定")
debug_mode = st.sidebar.checkbox("デバッグ表示ON", value=False)

hospital_name = st.text_input("病院名", placeholder="例：高雄病院")
prefecture = st.selectbox("都道府県（分かる場合のみ）", PREFECTURES, index=0)
main_url = st.text_input("病院URL（必須）", placeholder="https://...")

public_urls_raw = st.text_area(
    "公的ソースURL（任意・複数行可）",
    placeholder="例:\nhttps://...\nhttps://..."
)
recruit_urls_raw = st.text_area(
    "求人URL（任意・複数行可 / ハローワーク等も可）",
    placeholder="例:\nhttps://...\nhttps://..."
)
group_urls_raw = st.text_area(
    "グループ/法人URL（任意・複数行可）",
    placeholder="例:\nhttps://...\nhttps://..."
)
extra_official_urls_raw = st.text_area(
    "公式補助URL（任意・複数行可）",
    placeholder="例:\nhttps://...\nhttps://..."
)

if hospital_name.strip():
    helper = build_helper_links(hospital_name.strip(), prefecture)
    with st.expander("候補URLを探すための補助リンク"):
        st.markdown(f"[Google検索]({helper['google_search']})")
        st.markdown(f"[病院なび検索]({helper['byoinnavi_search']})")
        st.markdown(f"[Caloo検索]({helper['caloo_search']})")
        st.markdown(f"[QLife検索]({helper['qlife_search']})")

run = st.button("解析を実行", type="primary")

if run:
    if not hospital_name.strip():
        st.warning("病院名を入力してください。")
        st.stop()

    if not main_url.strip():
        st.warning("病院URLを入力してください。")
        st.stop()

    public_urls = parse_multiline_urls(public_urls_raw)
    recruit_urls = parse_multiline_urls(recruit_urls_raw)
    group_urls = parse_multiline_urls(group_urls_raw)
    extra_official_urls = parse_multiline_urls(extra_official_urls_raw)

    with st.spinner("病院URLを解析中..."):
        result = analyze_hospital_from_url(
            hospital_name=hospital_name.strip(),
            main_url=main_url.strip(),
            public_urls=public_urls,
            recruit_urls=recruit_urls,
            group_urls=group_urls,
            extra_official_urls=extra_official_urls,
            debug=debug_mode,
        )

    if result.get("status") == "error":
        st.error(result.get("error", "解析に失敗しました。"))
        if debug_mode:
            st.json(result.get("debug_info", {}))
        st.stop()

    st.subheader("① 病院基本情報 / 病院機能")
    basic = result.get("basic_info", {})

    def show_adopted_block(title: str, block: dict):
        st.write(f"**{title}**")
        st.write(f"- 最終判断: {block.get('adopted_value', '不明')}")
        st.write(f"- 整合性: {block.get('consistency', '不明')}")
        evidence = block.get("evidence", [])
        if evidence:
            st.write("- 根拠:")
            for ev in evidence[:5]:
                st.write(f"  - [{ev.get('source_type','不明')}] {ev.get('value','不明')} | {ev.get('url','')}")
        else:
            st.write("- 根拠: 不明")

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**病院名**: {result.get('hospital_name', '不明')}")
        st.write(f"**メインURL**: {result.get('main_url', '不明')}")
        st.write(f"**ソース種別**: {result.get('source_type', '不明')}")
        show_adopted_block("住所", basic.get("address", {}))
        show_adopted_block("地域", basic.get("region", {}))
        show_adopted_block("最寄駅", basic.get("nearest_station", {}))

    with c2:
        show_adopted_block("病床数", basic.get("bed_count", {}))
        show_adopted_block("診療科", basic.get("departments", {}))
        show_adopted_block("病院種別", basic.get("hospital_type", {}))
        hints = basic.get("function_hints", [])
        st.write("**病院機能の手掛かり**")
        if hints:
            for row in hints:
                st.write(f"- {row}")
        else:
            st.write("不明")

    st.subheader("② 施設基準 / 加算")
    facility = result.get("facility_info", {})
    st.write(f"**最終採用ソース**: {facility.get('adopted_source', '不明')}")
    st.write(f"**整合性**: {facility.get('consistency', '不明')}")

    st.write("**採用した入院料 / 基本料系**")
    adopted_basic_rates = facility.get("adopted_basic_rates", [])
    if adopted_basic_rates:
        for row in adopted_basic_rates:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**採用した加算系**")
    adopted_additions = facility.get("adopted_additions", [])
    if adopted_additions:
        for row in adopted_additions:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**公式HPで確認した施設基準関連**")
    official_confirmed_lines = facility.get("official_confirmed_lines", [])
    if official_confirmed_lines:
        for row in official_confirmed_lines[:30]:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**公的ソースで確認した施設基準関連**")
    public_confirmed_lines = facility.get("public_confirmed_lines", [])
    if public_confirmed_lines:
        for row in public_confirmed_lines[:30]:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.subheader("③ 求人窓口候補")
    contact = result.get("staff_contact_info", {})
    st.write(f"**最終採用ソース**: {contact.get('adopted_source', '不明')}")
    st.write(f"**整合性**: {contact.get('consistency', '不明')}")

    st.write("**採用した窓口候補の記載**")
    adopted_contact_lines = contact.get("adopted_contact_lines", [])
    if adopted_contact_lines:
        for row in adopted_contact_lines[:30]:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**採用した電話番号候補**")
    adopted_phones = contact.get("adopted_phones", [])
    if adopted_phones:
        for row in adopted_phones:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**採用したメール候補**")
    adopted_emails = contact.get("adopted_emails", [])
    if adopted_emails:
        for row in adopted_emails:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**公式ソースで確認した窓口候補**")
    for row in contact.get("official_contact_lines", [])[:20]:
        st.write(f"- {row}")

    st.write("**外部求人ソースで確認した窓口候補**")
    for row in contact.get("external_contact_lines", [])[:20]:
        st.write(f"- {row}")

    st.subheader("④ グループ情報候補")
    group = result.get("group_info", {})
    st.write(f"**整合性**: {group.get('consistency', '不明')}")
    candidates = group.get("candidates", [])
    if candidates:
        for row in candidates:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.subheader("⑤ 自動探索ページ一覧")
    discovered = result.get("discovered_pages", {})
    for cat in ["basic", "facility", "recruit", "group", "contact", "public"]:
        rows = discovered.get(cat, [])
        with st.expander(f"{cat} ({len(rows)}件)"):
            if rows:
                for row in rows:
                    st.write(f"- [{row.get('source_type','不明')}] {row.get('label', '')} | {row.get('url', '')}")
            else:
                st.write("該当なし")

    if debug_mode:
        st.subheader("デバッグ情報")
        st.json(result.get("debug_info", {}))
