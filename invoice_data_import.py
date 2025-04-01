import streamlit as st
import pandas as pd
from io import BytesIO 


def app2():
    st.title('請求書売上インポート')

    st.success('手順1)   下記表の該当する欄に「保険請求状況平均点」の「総点数」欄を入力')

    index = ["つくば", "羽生", "王子", "三鷹", "仙台", "川口", "船橋", "南森町", "高田馬場", "横浜関内", "福岡天神", "大宮"]
    columns = ['社保窓口入金', '国保窓口入金', '後期高齢']

    # 空のDataFrameを作成
    df = pd.DataFrame(index=index, columns=columns)

    # 編集用のデータエディタを配置
    edited_df = st.data_editor(df)

    # 現在の日付から1ヶ月前の月を取得
    one_month_ago = (pd.to_datetime("today") - pd.DateOffset(months=1)).month
    
    st.success('手順2)   対象の月を選択')

    # 月のリスト
    months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]

    # ユーザーから月を選択してもらう
    selected_month = st.selectbox("(初期値＝作業日の前月)", months, index=one_month_ago - 1)

    st.success('手順3)   仕訳の計上日を選択')

    # 発生日の選択
    year = pd.to_datetime("today").year
    default_last_day = pd.to_datetime(f"{year}-{selected_month[:-1]}-01") + pd.offsets.MonthEnd(0)
    selected_date = st.date_input("(初期値＝作業日の前月末日)", default_last_day.date())

    total_column = ['合計']
    check_df = pd.DataFrame(index=index, columns=total_column)

    st.success('手順4)   「仕訳作成」にチェック')

    if st.checkbox("仕訳作成"):
        df.update(edited_df, overwrite=True)
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))

        # 新しいDataFrameを作成し、元のデータと合計列を含める
        check_df = df.copy()  # 元のデータをコピー
        check_df['合計'] = df.sum(axis=1)  # 合計値を計算して新しい列に追加

        # 更新されたcheck_df DataFrameを表示
        st.write("データと合計:")
        st.dataframe(check_df)

        df = df.applymap(lambda x: x * 7 if pd.notna(x) and isinstance(x, (int, float)) else x)

        # '国保窓口入金' と '後期高齢' のどちらかまたは両方に入力があった場合の処理
        df['国保'] = df['国保窓口入金'].fillna(0) + df['後期高齢'].fillna(0)
        df.drop(['国保窓口入金', '後期高齢'], axis=1, inplace=True)
        df.rename(columns={'社保窓口入金': '社保'}, inplace=True)

        output_columns = ['収支区分', '発生日', '取引先', '税区分', '勘定科目', '品目', '部門', '金額']
        output_df = pd.DataFrame(columns=output_columns)

        # dfの値をoutput_dfに移す
        for col in df.columns:
            for idx in df.index:
                value = df.at[idx, col]

                if pd.isna(value):
                    value = None
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        continue  

                if value is not None and value != 0:
                    new_row = pd.DataFrame({'収支区分': ['収入'], '発生日': [selected_date], '取引先': [''], '税区分': ['非課売上'], '勘定科目': ['保険診療収入'], '品目': [col], '部門': [idx], '金額': [value]}, columns=output_columns)
                    output_df = pd.concat([output_df, new_row], ignore_index=True)

        st.write("仕訳作成:")
        st.dataframe(output_df)

        @st.cache_data
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data

        st.success('処理が完了しました')
        excel_data = convert_df_to_excel(output_df)
        st.download_button(
            label="ここからインポート用のエクセルをダウンロードしてください",
            data=excel_data,
            file_name='import_data(請求).xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
