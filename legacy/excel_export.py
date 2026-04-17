# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime

def export_excel(hospital, info, nursing, contact, acquired, missing):

    now = datetime.now().strftime("%Y%m%d_%H%M")

    filename = f"{hospital}_{now}.xlsx"

    writer = pd.ExcelWriter(filename, engine='openpyxl')

    # 病院基本情報
    df_info = pd.DataFrame([info])
    df_info.to_excel(writer, sheet_name="病院基本情報", index=False)

    # 看護配置
    df_nursing = pd.DataFrame([nursing])
    df_nursing.to_excel(writer, sheet_name="看護配置", index=False)

    # 採用窓口
    df_contact = pd.DataFrame([contact])
    df_contact.to_excel(writer, sheet_name="採用窓口", index=False)

    # 取得施設基準
    df_acquired = pd.DataFrame(acquired, columns=["取得施設基準"])
    df_acquired.to_excel(writer, sheet_name="取得施設基準", index=False)

    # 未取得
    df_missing = pd.DataFrame(missing, columns=["施設基準","点数"])
    df_missing.to_excel(writer, sheet_name="未取得施設基準", index=False)

    writer.close()

    return filename
