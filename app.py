# app.py
# -*- coding: utf-8 -*-

import streamlit as st

from hospital_basic import search_hospital_phase, identify_from_selected_candidate


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
st.error("BUILD MARKER: 2026-04-17 11:40")
st.caption("まずは『病院検索 → 候補選択 → 病院特定』を安定化する版")

if "search_result" not in st.session_state:
    st.session_state.search_result = None

st.sidebar.header("設定")
debug_mode = st.sidebar.checkbox("デバッグ表示ON", value=False)

hospital_name = st.text_input("病院名を入力してください", placeholder="例：高雄病院")
prefecture = st.selectbox("都道府県（分かる場合のみ）", PREFECTURES, index=0)

run_search = st.button("① 病院候補を検索", type="primary")

if run_search:
    if not hospital_name.strip():
        st.warning("病院名を入力してください。")
        st.stop()

    with st.spinner("候補URL検索中..."):
        st.session_state.search_result = search_hospital_phase(
            hospital_name=hospital_name.strip(),
            prefecture=prefecture,
            debug=debug_mode,
        )

st.subheader("① 病院検索")

search_result = st.session_state.search_result

if search_result:
    if search_result.get("status") == "not_found":
        st.error("有効な候補URLが見つかりませんでした。")
        if debug_mode:
            st.subheader("デバッグ情報")
            st.json(search_result.get("debug_info", {}))
    else:
        candidates = search_result.get("candidates", [])
        st.success(f"候補URLを {len(candidates)} 件取得しました。")

        options = []
        url_map = {}

        for i, c in enumerate(candidates, start=1):
            label = f"{i}. [{c.get('source_type','不明')}] {c.get('title','無題')} | {c.get('url','')}"
            options.append(label)
            url_map[label] = c.get("url", "")

        selected_label = st.selectbox("② 候補を選択してください", options)
        selected_url = url_map[selected_label]

        candidate_rows = []
        for i, c in enumerate(candidates, start=1):
            candidate_rows.append({
                "No": i,
                "source_type": c.get("source_type", ""),
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "provider": c.get("provider", ""),
                "query": c.get("query", ""),
                "internal_score": c.get("internal_score", 0),
            })
        st.dataframe(candidate_rows, use_container_width=True)

        run_identify = st.button("③ 選択候補で病院特定")

        st.subheader("② 病院特定結果")
        if run_identify:
            with st.spinner("選択候補を解析中..."):
                result = identify_from_selected_candidate(
                    hospital_name=hospital_name.strip(),
                    selected_url=selected_url,
                    prefecture=prefecture,
                    debug=debug_mode,
                )

            if result.get("status") == "ok":
                st.success("選択候補の解析に成功しました。")
            elif result.get("status") == "low_confidence":
                st.warning("候補は解析できましたが、住所等の抽出がまだ弱いです。")
            else:
                st.error("選択候補を特定できませんでした。")

            selected = result.get("selected")
            if selected:
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**暫定候補タイトル**: {selected.get('title', '不明')}")
                    st.write(f"**URL**: {selected.get('url', '不明')}")
                    st.write(f"**ソース種別**: {selected.get('source_type', '不明')}")
                    st.write(f"**スコア**: {selected.get('score', '不明')}")

                with c2:
                    st.write(f"**住所**: {selected.get('address', '不明')}")
                    st.write(f"**地域**: {selected.get('region', '不明')}")
                    st.write(f"**最寄駅**: {selected.get('nearest_station', '不明')}")
                    st.write(f"**病床数**: {selected.get('bed_count', '不明')}")
                    st.write(f"**診療科**: {selected.get('departments', '不明')}")
                    st.write(f"**病院種別**: {selected.get('hospital_type', '不明')}")

            st.subheader("③ 施設基準等検索")
            if result.get("status") == "ok":
                st.info("次の段階へ進めますが、今回はまだ未実装です。")
            else:
                st.warning("病院特定が不十分なため、施設基準等検索には進めません。")

            if debug_mode:
                st.subheader("デバッグ情報")
                st.json(result.get("debug_info", {}))

        elif debug_mode:
            st.subheader("デバッグ情報")
            st.json(search_result.get("debug_info", {}))
