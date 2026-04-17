# app.py
# -*- coding: utf-8 -*-

import json
import streamlit as st

from analyzer.report import run_analysis_report


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


def parse_multiline_urls(raw_text: str) -> list[str]:
    if not raw_text:
        return []

    urls: list[str] = []
    seen = set()

    for line in raw_text.splitlines():
        value = line.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        urls.append(value)

    return urls


def safe_get(d: dict, key: str, default=None):
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def render_final_block(title: str, block: dict):
    st.write(f"**{title}**")

    if not isinstance(block, dict):
        st.write("- ① 最終判断: 不明")
        st.write("- ② 根拠ソース: 不明")
        st.write("- ③ 整合性: 不明")
        st.write("- ④ コメント: 不明")
        return

    final_value = block.get("final_value", "不明")
    consistency = block.get("consistency", "不明")
    comment = block.get("comment", "不明")
    evidence = block.get("evidence", [])

    st.write(f"- ① 最終判断: {final_value}")
    st.write("- ② 根拠ソース:")

    if evidence:
        for ev in evidence[:8]:
            source_label = ev.get("source_label", "不明")
            source_type = ev.get("source_type", "不明")
            url = ev.get("url", "")
            value = ev.get("value", "不明")
            st.write(f"  - [{source_type}] {source_label} | {value} | {url}")
    else:
        st.write("  - 不明")

    st.write(f"- ③ 整合性: {consistency}")
    st.write(f"- ④ コメント: {comment}")


def render_list_section(title: str, rows: list):
    st.write(f"**{title}**")
    if rows:
        for row in rows:
            st.write(f"- {row}")
    else:
        st.write("不明")


st.set_page_config(
    page_title="ルフト病院分析AI",
    page_icon="🏥",
    layout="wide",
)

st.title("ルフト病院分析AI")
st.caption("無料前提 / 病院URL起点 / 複数ソース比較 / 不明優先の安全設計")

st.sidebar.header("設定")
debug_mode = st.sidebar.checkbox("デバッグ表示ON", value=False)
max_pages = st.sidebar.slider("同一ドメイン巡回上限", min_value=5, max_value=40, value=15, step=1)
timeout_sec = st.sidebar.slider("HTTPタイムアウト秒", min_value=5, max_value=30, value=12, step=1)

hospital_name = st.text_input("病院名", placeholder="例：高雄病院")
prefecture = st.selectbox("都道府県（分かる場合のみ）", PREFECTURES, index=0)
main_url = st.text_input("病院URL（必須）", placeholder="https://...")

public_urls_raw = st.text_area(
    "公的ソースURL（任意・複数行可）",
    placeholder="例:\nhttps://...\nhttps://..."
)
recruit_urls_raw = st.text_area(
    "求人URL（任意・複数行可）",
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

    with st.spinner("解析中です。病院URL配下と候補ソースを確認しています..."):
        result = run_analysis_report(
            hospital_name=hospital_name.strip(),
            main_url=main_url.strip(),
            prefecture=prefecture.strip(),
            public_urls=public_urls,
            recruit_urls=recruit_urls,
            group_urls=group_urls,
            extra_official_urls=extra_official_urls,
            max_pages=max_pages,
            timeout_sec=timeout_sec,
            debug=debug_mode,
        )

    if safe_get(result, "status") == "error":
        st.error(safe_get(result, "error", "解析に失敗しました。"))
        if debug_mode:
            st.subheader("デバッグ情報")
            st.json(safe_get(result, "debug_info", {}))
        st.stop()

    st.success("解析が完了しました。")

    summary = safe_get(result, "summary", {})
    discovered = safe_get(result, "discovered_pages", {})
    basic = safe_get(result, "basic_info", {})
    facility = safe_get(result, "facility_info", {})
    recruit = safe_get(result, "recruit_info", {})
    group = safe_get(result, "group_info", {})
    contacts = safe_get(result, "contact_info", {})

    st.subheader("0. 解析対象サマリー")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**病院名**: {safe_get(summary, 'hospital_name', '不明')}")
        st.write(f"**都道府県**: {safe_get(summary, 'prefecture', '不明')}")
        st.write(f"**メインURL**: {safe_get(summary, 'main_url', '不明')}")
    with col2:
        st.write(f"**巡回ページ数**: {safe_get(summary, 'crawled_pages_count', 0)}")
        st.write(f"**抽出候補ページ数**: {safe_get(summary, 'candidate_pages_count', 0)}")
        st.write(f"**外部候補ページ数**: {safe_get(summary, 'external_pages_count', 0)}")

    st.subheader("1. 病院基本情報")
    left, right = st.columns(2)

    with left:
        render_final_block("住所", safe_get(basic, "address", {}))
        render_final_block("地域", safe_get(basic, "region", {}))
        render_final_block("最寄駅", safe_get(basic, "nearest_station", {}))
        render_final_block("法人名", safe_get(basic, "corporation_name", {}))
        render_final_block("代表電話", safe_get(basic, "phone", {}))
        render_final_block("代表メール", safe_get(basic, "email", {}))

    with right:
        render_final_block("病床数", safe_get(basic, "bed_count", {}))
        render_final_block("診療科", safe_get(basic, "departments", {}))
        render_final_block("病院種別", safe_get(basic, "hospital_type", {}))
        render_final_block("病院機能", safe_get(basic, "hospital_function", {}))

    st.subheader("2. 施設基準・届出・加算")
    render_final_block("施設基準総合判断", safe_get(facility, "overall", {}))
    render_list_section("基本料系", safe_get(facility, "basic_rates", []))
    render_list_section("加算系", safe_get(facility, "additions", []))
    render_list_section("根拠行（公式）", safe_get(facility, "official_lines", []))
    render_list_section("根拠行（公的）", safe_get(facility, "public_lines", []))

    st.subheader("3. 求人窓口")
    render_final_block("採用担当候補", safe_get(recruit, "contact_person", {}))
    render_final_block("担当部署候補", safe_get(recruit, "department", {}))
    render_final_block("問い合わせ電話", safe_get(recruit, "phone", {}))
    render_final_block("問い合わせメール", safe_get(recruit, "email", {}))
    render_list_section("求人記載行", safe_get(recruit, "contact_lines", []))

    st.subheader("4. グループ情報")
    render_final_block("同一法人 / 同一グループ総合判断", safe_get(group, "overall", {}))
    render_list_section("関連施設候補", safe_get(group, "related_facilities", []))
    render_list_section("勤務地・法人候補", safe_get(group, "group_lines", []))

    st.subheader("5. 連絡先抽出")
    render_final_block("代表電話候補", safe_get(contacts, "phone", {}))
    render_final_block("代表メール候補", safe_get(contacts, "email", {}))
    render_list_section("問い合わせ関連行", safe_get(contacts, "contact_lines", []))

    st.subheader("6. 自動探索ページ一覧")
    for category in ["basic", "facility", "recruit", "group", "contact", "public"]:
        rows = safe_get(discovered, category, [])
        with st.expander(f"{category} ({len(rows)})"):
            if rows:
                for row in rows:
                    label = row.get("label", "")
                    source_type = row.get("source_type", "不明")
                    url = row.get("url", "")
                    st.write(f"- [{source_type}] {label} | {url}")
            else:
                st.write("該当なし")

    st.subheader("7. JSON出力")
    json_text = json.dumps(result, ensure_ascii=False, indent=2)
    st.download_button(
        label="解析結果JSONをダウンロード",
        data=json_text,
        file_name="luft_hospital_analysis_result.json",
        mime="application/json",
    )

    if debug_mode:
        st.subheader("8. デバッグ情報")
        st.json(safe_get(result, "debug_info", {}))
