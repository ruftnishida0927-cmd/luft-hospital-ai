# app.py
# -*- coding: utf-8 -*-

import streamlit as st

from hospital_basic import identify_hospital_basic


st.set_page_config(
    page_title="ルフト病院分析AI",
    page_icon="🏥",
    layout="wide",
)

st.title("ルフト病院分析AI")
st.error("BUILD MARKER: 2026-04-16 11:20")
st.caption("まずは「病院検索 → 病院特定」を安定化する版")


def show_basic_result(result: dict):
    status = result.get("status", "unknown")
    selected = result.get("selected")

    st.subheader("② 病院特定結果")

    if status == "ok" and selected:
        st.success("病院特定に成功しました。")

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**入力病院名**: {selected.get('hospital_name_input', '不明')}")
            st.write(f"**参照タイトル**: {selected.get('title', '不明')}")
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

        st.info("③ 施設基準等検索には進める状態です。")

    elif status in ["ambiguous", "low_confidence"] and selected:
        st.warning("病院候補は見つかりましたが、まだ特定精度が不十分です。施設基準検索には進めません。")

        st.write(f"**暫定候補タイトル**: {selected.get('title', '不明')}")
        st.write(f"**URL**: {selected.get('url', '不明')}")
        st.write(f"**住所**: {selected.get('address', '不明')}")
        st.write(f"**地域**: {selected.get('region', '不明')}")
        st.write(f"**最寄駅**: {selected.get('nearest_station', '不明')}")
        st.write(f"**病床数**: {selected.get('bed_count', '不明')}")
        st.write(f"**診療科**: {selected.get('departments', '不明')}")
        st.write(f"**病院種別**: {selected.get('hospital_type', '不明')}")
        st.write(f"**スコア**: {selected.get('score', '不明')}")

    else:
        st.error("病院候補を特定できませんでした。")


def show_candidate_table(result: dict):
    candidates = result.get("candidates", [])
    if not candidates:
        return

    st.subheader("候補URL一覧")
    rows = []
    for i, c in enumerate(candidates, start=1):
        facts = c.get("facts", {})
        rows.append({
            "No": i,
            "score": c.get("score", 0),
            "source_type": c.get("source_type", ""),
            "title": c.get("title", ""),
            "url": c.get("url", ""),
            "address": facts.get("address", "不明"),
            "region": facts.get("region", "不明"),
            "nearest_station": facts.get("nearest_station", "不明"),
            "bed_count": facts.get("bed_count", "不明"),
        })

    st.dataframe(rows, use_container_width=True)


def show_debug(result: dict):
    debug_info = result.get("debug_info", {})
    if not debug_info:
        return

    st.subheader("デバッグ情報")
    st.json(debug_info)


st.sidebar.header("設定")
debug_mode = st.sidebar.checkbox("デバッグ表示ON", value=False)

hospital_name = st.text_input("病院名を入力してください", placeholder="例：高雄病院")

run = st.button("病院検索を実行", type="primary")

if run:
    if not hospital_name.strip():
        st.warning("病院名を入力してください。")
        st.stop()

    st.subheader("① 病院検索")
    with st.spinner("検索・候補統合中..."):
        try:
            result = identify_hospital_basic(hospital_name.strip(), debug=debug_mode)
        except Exception as e:
            st.error(f"処理中にエラーが発生しました: {e}")
            st.stop()

    show_basic_result(result)
    show_candidate_table(result)

    if debug_mode:
        show_debug(result)

    st.subheader("③ 施設基準等検索")
    if result.get("status") == "ok":
        st.info("次の段階へ進めますが、今回はまだ未実装です。病院特定が安定してから facility_standard.py を接続してください。")
    else:
        st.warning("病院特定が不十分なため、施設基準等検索には進めません。")
