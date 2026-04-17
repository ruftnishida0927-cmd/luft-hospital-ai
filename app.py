# app.py
# -*- coding: utf-8 -*-

import streamlit as st

from hospital_basic import analyze_hospital_from_url
from source_hospital import build_helper_links


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
st.caption("無料前提のURL解析版")

st.sidebar.header("設定")
debug_mode = st.sidebar.checkbox("デバッグ表示ON", value=False)

hospital_name = st.text_input("病院名", placeholder="例：高雄病院")
prefecture = st.selectbox("都道府県（分かる場合のみ）", PREFECTURES, index=0)
main_url = st.text_input("病院URL（必須）", placeholder="https://...")
recruit_url = st.text_input("求人URL（任意）", placeholder="https://...")

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

    with st.spinner("病院URLを解析中..."):
        result = analyze_hospital_from_url(
            hospital_name=hospital_name.strip(),
            main_url=main_url.strip(),
            recruit_url=recruit_url.strip(),
            debug=debug_mode,
        )

    st.subheader("① 病院基本情報 / 病院機能")
    basic = result.get("basic_info", {})

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**病院名**: {result.get('hospital_name', '不明')}")
        st.write(f"**メインURL**: {result.get('main_url', '不明')}")
        st.write(f"**ソース種別**: {result.get('source_type', '不明')}")
        st.write(f"**住所**: {basic.get('address', '不明')}")
        st.write(f"**地域**: {basic.get('region', '不明')}")

    with c2:
        st.write(f"**最寄駅**: {basic.get('nearest_station', '不明')}")
        st.write(f"**病床数**: {basic.get('bed_count', '不明')}")
        st.write(f"**診療科**: {basic.get('departments', '不明')}")
        st.write(f"**病院種別**: {basic.get('hospital_type', '不明')}")
        hints = basic.get("function_hints", [])
        st.write(f"**病院機能の手掛かり**: {'、'.join(hints) if hints else '不明'}")

    st.subheader("② 施設基準 / 加算")
    facility = result.get("facility_info", {})
    if facility.get("status") == "ok":
        st.success("施設基準 / 加算に関する記載を検出しました。")
    else:
        st.warning("施設基準 / 加算の記載を確認できませんでした。")

    st.write("**入院料 / 基本料系**")
    basic_rates = facility.get("basic_rates", [])
    if basic_rates:
        for row in basic_rates:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**加算系**")
    additions = facility.get("additions", [])
    if additions:
        for row in additions:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**その他の届出・掲示事項候補**")
    other_items = facility.get("other_items", [])
    if other_items:
        for row in other_items:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.subheader("③ 求人窓口候補")
    contact = result.get("staff_contact_info", {})
    if contact.get("status") == "ok":
        st.success("採用窓口候補を検出しました。")
    else:
        st.warning("採用窓口候補を確認できませんでした。")

    st.write("**窓口候補の記載**")
    contact_lines = contact.get("contact_lines", [])
    if contact_lines:
        for row in contact_lines:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**電話番号候補**")
    phones = contact.get("phones", [])
    if phones:
        for row in phones:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.write("**メール候補**")
    emails = contact.get("emails", [])
    if emails:
        for row in emails:
            st.write(f"- {row}")
    else:
        st.write("不明")

    st.subheader("④ グループ情報候補")
    group = result.get("group_info", {})
    if group.get("status") == "ok":
        st.success("グループ/法人関連の記載を検出しました。")
        for row in group.get("candidates", []):
            st.write(f"- {row}")
    else:
        st.warning("グループ情報を確認できませんでした。")

    st.subheader("⑤ 自動探索ページ一覧")
    discovered = result.get("discovered_pages", {})
    for cat in ["basic", "facility", "recruit", "group", "contact"]:
        rows = discovered.get(cat, [])
        with st.expander(f"{cat} ({len(rows)}件)"):
            if rows:
                for row in rows:
                    st.write(f"- {row.get('label', '')} | {row.get('url', '')}")
            else:
                st.write("該当なし")

    if debug_mode:
        st.subheader("デバッグ情報")
        st.json(result.get("debug_info", {}))
