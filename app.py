import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from openai import OpenAI
from datetime import datetime

Path("data").mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="個人財務 Dashboard",
    page_icon="💰",
    layout="wide"
)

st.title("💰 個人財務 Dashboard")
privacy_mode = st.sidebar.checkbox("🔒 隱私模式：隱藏金額", value=False)


monthly_expense = st.sidebar.number_input(
    "每月生活支出",
    min_value=0,
    value=50000,
    step=1000
)

monthly_saving = st.sidebar.number_input(
    "每月儲蓄 / 投資金額",
    min_value=0,
    value=30000,
    step=1000
)

def money(value):
    if privacy_mode:
        return "NT$•••"
    return f"NT${value:,.0f}"


def percent(value):
    return f"{value:.2f}%"


def clean_number(value):
    """把 NT$、逗號、百分比清掉，轉成數字"""
    if pd.isna(value):
        return 0

    text = str(value)
    text = text.replace("NT$", "")
    text = text.replace(",", "")
    text = text.replace("%", "")
    text = text.strip()

    try:
        return float(text)
    except ValueError:
        return 0


dashboard_csv_url = st.secrets.get("DASHBOARD_CSV_URL", "")

if dashboard_csv_url:
    cache_buster = datetime.now().timestamp()
    separator = "&" if "?" in dashboard_csv_url else "?"
    fresh_dashboard_url = f"{dashboard_csv_url}{separator}cache_bust={cache_buster}"

    df = pd.read_csv(fresh_dashboard_url, header=None)
    dashboard_source = "Google Sheets URL"
else:
    csv_path = Path("data/dashboard.csv")

    if not csv_path.exists():
        st.error("找不到 data/dashboard.csv，也沒有設定 DASHBOARD_CSV_URL。")
        st.stop()

    df = pd.read_csv(csv_path, header=None)
    dashboard_source = "本機 CSV"

st.sidebar.caption(f"Dashboard 資料來源：{dashboard_source}")

# 左側核心指標：A欄是名稱，B欄是數值
metrics = {}

for i in range(len(df)):
    name = df.iloc[i, 0] if df.shape[1] > 0 else None
    value = df.iloc[i, 1] if df.shape[1] > 1 else None

    if pd.notna(name):
        metrics[str(name)] = clean_number(value)


total_cash = metrics.get("總現金", 0)
total_assets = metrics.get("總資產", 0)
total_debt = metrics.get("總負債", 0)
net_worth = metrics.get("淨值", 0)
stock_value = metrics.get("股票市值", 0)
stock_profit = metrics.get("股票損益", 0)
debt_ratio = metrics.get("負債比", 0)
cash_ratio = metrics.get("現金比例", 0)
annual_dividend = metrics.get("年股息", 0)
monthly_passive_income = metrics.get("月被動收入", 0)


st.subheader("📊 核心財務指標")

col1, col2, col3 = st.columns(3)

col1.metric("總資產", money(total_assets))
col2.metric("總負債", money(total_debt))
col3.metric("淨值", money(net_worth))

col4, col5, col6 = st.columns(3)

col4.metric("總現金", money(total_cash))
col5.metric("股票市值", money(stock_value))
col6.metric("股票損益", money(stock_profit))

col7, col8 = st.columns(2)

col7.metric("負債比", percent(debt_ratio))
col8.metric("現金比例", percent(cash_ratio))

st.subheader("💵 被動收入")

col9, col10 = st.columns(2)

col9.metric("年股息", money(annual_dividend))
col10.metric("月被動收入", money(monthly_passive_income))


# 右側資產配置：D欄是資產類型，E欄是金額
allocation_data = []

if df.shape[1] >= 5:
    for i in range(len(df)):
        asset_name = df.iloc[i, 3]
        asset_value = df.iloc[i, 4]

        if pd.notna(asset_name):
            allocation_data.append({
                "資產類型": str(asset_name),
                "金額": clean_number(asset_value)
            })

allocation_df = pd.DataFrame(allocation_data)
allocation_df = allocation_df[allocation_df["金額"] > 0]

st.subheader("🩺 財務健康診斷")

score = 100
diagnosis_items = []


def add_diagnosis(level, title, message, penalty=0):
    global score
    diagnosis_items.append({
        "level": level,
        "title": title,
        "message": message,
        "penalty": penalty
    })


def get_asset_value(asset_name):
    if allocation_df.empty:
        return 0

    matched = allocation_df[allocation_df["資產類型"] == asset_name]

    if matched.empty:
        return 0

    return matched["金額"].sum()


# 1. 負債比診斷
if debt_ratio >= 70:
    score -= 25
    add_diagnosis(
        "danger",
        "負債比過高",
        f"目前負債比為 {debt_ratio:.2f}%，財務槓桿偏高，建議優先降低負債。",
        25
    )
elif debt_ratio >= 60:
    score -= 15
    add_diagnosis(
        "warning",
        "負債比偏高",
        f"目前負債比為 {debt_ratio:.2f}%，仍可承受，但需要持續降低負債。",
        15
    )
else:
    add_diagnosis(
        "success",
        "負債比可控",
        f"目前負債比為 {debt_ratio:.2f}%，整體槓桿風險相對可控。",
        0
    )


# 2. 現金比例診斷
if cash_ratio < 5:
    score -= 20
    add_diagnosis(
        "danger",
        "現金比例過低",
        f"目前現金比例只有 {cash_ratio:.2f}%，流動性偏低，建議提高緊急預備金。",
        20
    )
elif cash_ratio < 10:
    score -= 10
    add_diagnosis(
        "warning",
        "現金比例偏低",
        f"目前現金比例為 {cash_ratio:.2f}%，建議逐步提高現金水位。",
        10
    )
else:
    add_diagnosis(
        "success",
        "現金比例健康",
        f"目前現金比例為 {cash_ratio:.2f}%，流動性狀況良好。",
        0
    )


# 3. 房地產集中度診斷
real_estate_value = get_asset_value("房地產")
real_estate_ratio = real_estate_value / total_assets * 100 if total_assets > 0 else 0

if real_estate_ratio >= 80:
    score -= 15
    add_diagnosis(
        "warning",
        "房地產占比過高",
        f"房地產占總資產 {real_estate_ratio:.2f}%，資產集中度偏高。",
        15
    )
elif real_estate_ratio >= 60:
    score -= 8
    add_diagnosis(
        "info",
        "房地產占比較高",
        f"房地產占總資產 {real_estate_ratio:.2f}%，建議未來增加流動性資產。",
        8
    )
else:
    add_diagnosis(
        "success",
        "資產集中度較健康",
        f"房地產占總資產 {real_estate_ratio:.2f}%，集中風險較低。",
        0
    )


# 4. 股票比例診斷
stock_ratio = stock_value / total_assets * 100 if total_assets > 0 else 0

if stock_ratio < 5:
    score -= 10
    add_diagnosis(
        "info",
        "股票配置偏低",
        f"股票占總資產 {stock_ratio:.2f}%，市場參與度偏低。",
        10
    )
elif stock_ratio <= 30:
    add_diagnosis(
        "success",
        "股票配置合理",
        f"股票占總資產 {stock_ratio:.2f}%，配置相對穩健。",
        0
    )
else:
    score -= 8
    add_diagnosis(
        "warning",
        "股票配置偏高",
        f"股票占總資產 {stock_ratio:.2f}%，需注意市場波動風險。",
        8
    )


# 5. 被動收入診斷
if monthly_passive_income < 1000:
    score -= 10
    add_diagnosis(
        "info",
        "被動收入仍低",
        f"目前月被動收入約 {money(monthly_passive_income)}，距離覆蓋生活支出仍有一段距離。",
        10
    )
else:
    add_diagnosis(
        "success",
        "已有初步被動收入",
        f"目前月被動收入約 {money(monthly_passive_income)}，已開始建立現金流。",
        0
    )


score = max(score, 0)

if score >= 85:
    grade = "A"
    grade_message = "財務體質良好"
elif score >= 70:
    grade = "B"
    grade_message = "財務體質尚可，但仍有改善空間"
elif score >= 55:
    grade = "C"
    grade_message = "財務風險偏高，需要調整"
else:
    grade = "D"
    grade_message = "財務壓力較高，建議優先處理風險"


col_score1, col_score2 = st.columns(2)

col_score1.metric("財務健康分數", f"{score}/100")
col_score2.metric("財務評級", grade)

st.write(f"### {grade_message}")

for item in diagnosis_items:
    if item["level"] == "success":
        st.success(f"✅ {item['title']}：{item['message']}")
    elif item["level"] == "warning":
        st.warning(f"⚠️ {item['title']}：{item['message']}")
    elif item["level"] == "danger":
        st.error(f"🚨 {item['title']}：{item['message']}")
    else:
        st.info(f"ℹ️ {item['title']}：{item['message']}")

st.subheader("🎯 優先行動建議")

action_plan = []

if cash_ratio < 5:
    action_plan.append("優先提高現金水位，目標先讓現金比例提升到 5% 以上。")

if debt_ratio >= 60:
    action_plan.append("暫緩增加高風險投資，優先降低負債比，尤其是高利率負債。")

if real_estate_ratio >= 80:
    action_plan.append("未來新增資金應優先配置到現金、股票或其他流動性資產，降低房地產集中風險。")

if stock_ratio < 5:
    action_plan.append("若風險承受度允許，可逐步建立股票或 ETF 部位，提高長期市場參與度。")

if monthly_passive_income < 1000:
    action_plan.append("建立股息或利息收入目標，先以月被動收入 NT$1,000 作為第一階段目標。")

if len(action_plan) == 0:
    st.success("目前沒有明顯重大風險，建議維持紀律並持續追蹤淨值成長。")
else:
    for i, action in enumerate(action_plan, start=1):
        st.write(f"{i}. {action}")

st.subheader("🔥 FIRE 財務自由進度")

annual_expense = monthly_expense * 12
fire_target = annual_expense * 25
fire_progress = net_worth / fire_target * 100 if fire_target > 0 else 0
gap_to_fire = fire_target - net_worth

col_fire1, col_fire2, col_fire3 = st.columns(3)

col_fire1.metric("年支出", money(annual_expense))
col_fire2.metric("FIRE 目標資產", money(fire_target))
col_fire3.metric("FIRE 完成率", f"{fire_progress:.2f}%")

st.progress(min(fire_progress / 100, 1.0))

if gap_to_fire > 0:
    st.info(f"距離 FIRE 目標還差 {money(gap_to_fire)}。")
else:
    st.success("你已經達到 FIRE 目標資產。")


st.subheader("🔮 財富趨勢預測")

years = list(range(0, 21))
annual_saving = monthly_saving * 12

scenarios = {
    "保守 3%": 0.03,
    "中性 5%": 0.05,
    "積極 8%": 0.08,
}

projection_data = []

for year in years:
    row = {"年份": year}

    for scenario_name, annual_return in scenarios.items():
        if year == 0:
            future_value = net_worth
        else:
            investment_growth = net_worth * ((1 + annual_return) ** year)
            saving_growth = annual_saving * (((1 + annual_return) ** year - 1) / annual_return)
            future_value = investment_growth + saving_growth

        row[scenario_name] = future_value

    projection_data.append(row)

projection_df = pd.DataFrame(projection_data)

if privacy_mode:
    st.info("隱私模式已開啟，財富預測金額圖已隱藏。")
else:
    col_projection1, col_projection2, col_projection3 = st.columns(3)

    value_5y = projection_df.loc[projection_df["年份"] == 5, "中性 5%"].values[0]
    value_10y = projection_df.loc[projection_df["年份"] == 10, "中性 5%"].values[0]
    value_20y = projection_df.loc[projection_df["年份"] == 20, "中性 5%"].values[0]

    col_projection1.metric("5 年後淨值估算", money(value_5y))
    col_projection2.metric("10 年後淨值估算", money(value_10y))
    col_projection3.metric("20 年後淨值估算", money(value_20y))

    fig_projection = px.line(
        projection_df,
        x="年份",
        y=["保守 3%", "中性 5%", "積極 8%"],
        markers=True,
        title="未來 1～20 年財富成長預測",
        labels={
            "value": "預估淨值（TWD）",
            "variable": "情境",
            "年份": "年"
        }
    )

    st.plotly_chart(fig_projection, use_container_width=True)

    display_projection_df = projection_df.copy()
    for col in ["保守 3%", "中性 5%", "積極 8%"]:
        display_projection_df[col] = display_projection_df[col].map(lambda x: f"NT${x:,.0f}")

    st.dataframe(display_projection_df, use_container_width=True)

st.subheader("⏳ FIRE 達成年限預估")

fire_year_results = []

for scenario_name in ["保守 3%", "中性 5%", "積極 8%"]:
    reached_rows = projection_df[projection_df[scenario_name] >= fire_target]

    if reached_rows.empty:
        fire_year_results.append({
            "情境": scenario_name,
            "預估達成年限": "20 年內尚未達成"
        })
    else:
        reached_year = int(reached_rows.iloc[0]["年份"])
        fire_year_results.append({
            "情境": scenario_name,
            "預估達成年限": f"{reached_year} 年"
        })

fire_year_df = pd.DataFrame(fire_year_results)

st.dataframe(fire_year_df, use_container_width=True)

st.subheader("🧩 資產配置")

if not allocation_df.empty:
    fig = px.pie(
        allocation_df,
        names="資產類型",
        values="金額",
        title="資產配置比例"
    )
    st.plotly_chart(fig, use_container_width=True)

    if privacy_mode:
        display_df = allocation_df.copy()
        total = display_df["金額"].sum()
        display_df["比例"] = display_df["金額"] / total * 100
        display_df = display_df[["資產類型", "比例"]]
        display_df["比例"] = display_df["比例"].map(lambda x: f"{x:.2f}%")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.dataframe(allocation_df, use_container_width=True)
else:
    st.warning("找不到資產配置資料，請確認 Dashboard 的 D:E 欄有資料。")

st.subheader("📈 淨值歷史趨勢")

history_csv_url = st.secrets.get("NET_WORTH_HISTORY_CSV_URL", "")
history_local_path = Path("data/net_worth_history.csv")

if history_csv_url:
    cache_buster = datetime.now().timestamp()
    separator = "&" if "?" in history_csv_url else "?"
    fresh_history_url = f"{history_csv_url}{separator}cache_bust={cache_buster}"

    history_df = pd.read_csv(fresh_history_url)
    history_source = "Google Sheets URL"

elif history_local_path.exists():
    history_df = pd.read_csv(history_local_path)
    history_source = "本機 CSV"

else:
    history_df = None
    history_source = "無資料"

st.sidebar.caption(f"淨值歷史資料來源：{history_source}")

if history_df is None:
    st.warning("找不到淨值歷史資料。請設定 NET_WORTH_HISTORY_CSV_URL 或放入 data/net_worth_history.csv。")

else:
    # 清理欄位名稱
    history_df.columns = [str(col).strip() for col in history_df.columns]

    if "日期" not in history_df.columns:
        st.error("淨值歷史 CSV 找不到「日期」欄位。")

    else:
        history_df["日期"] = pd.to_datetime(history_df["日期"], errors="coerce")

        numeric_columns = [
            "總現金",
            "總資產",
            "總負債",
            "淨值",
            "股票市值",
            "負債比",
            "現金比例",
        ]

        for col in numeric_columns:
            if col in history_df.columns:
                history_df[col] = history_df[col].apply(clean_number)

        history_df = history_df.dropna(subset=["日期"])

        chart_columns = [
            col for col in ["總資產", "總負債", "淨值", "股票市值"]
            if col in history_df.columns
        ]

        if len(history_df) == 0:
            st.warning("淨值歷史表沒有有效日期資料。")

        elif len(chart_columns) == 0:
            st.warning("淨值歷史表找不到可畫圖的欄位。")

        else:
            if privacy_mode:
                st.info("隱私模式已開啟，淨值歷史金額圖已隱藏。")

            else:
                fig_history = px.line(
                    history_df,
                    x="日期",
                    y=chart_columns,
                    markers=True,
                    title="淨值 / 總資產 / 總負債 趨勢",
                    labels={
                        "value": "金額（TWD）",
                        "variable": "指標",
                        "日期": "日期",
                    },
                )

                st.plotly_chart(fig_history, use_container_width=True)
                st.dataframe(history_df, use_container_width=True)

st.subheader("🤖 GPT 財務顧問")

financial_summary = f"""
這是一份個人財務摘要，請根據資料提供財務分析。

核心資料：
- 總資產：NT${total_assets:,.0f}
- 總負債：NT${total_debt:,.0f}
- 淨值：NT${net_worth:,.0f}
- 總現金：NT${total_cash:,.0f}
- 股票市值：NT${stock_value:,.0f}
- 股票損益：NT${stock_profit:,.0f}
- 負債比：{debt_ratio:.2f}%
- 現金比例：{cash_ratio:.2f}%
- 年股息：NT${annual_dividend:,.0f}
- 月被動收入：NT${monthly_passive_income:,.0f}

資產配置：
- 房地產比例：約 {real_estate_ratio:.2f}%
- 股票比例：約 {stock_ratio:.2f}%

財務診斷：
- 財務健康分數：{score}/100
- 財務評級：{grade}

FIRE：
- 每月生活支出：NT${monthly_expense:,.0f}
- 每月儲蓄 / 投資金額：NT${monthly_saving:,.0f}
- 年支出：NT${annual_expense:,.0f}
- FIRE 目標資產：NT${fire_target:,.0f}
- FIRE 完成率：{fire_progress:.2f}%
- 距離 FIRE：NT${gap_to_fire:,.0f}
"""

with st.expander("查看送給 GPT 的財務摘要"):
    if privacy_mode:
        st.info("隱私模式已開啟，GPT 輸入摘要已隱藏。")
    else:
        st.text(financial_summary)


ai_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_rating": {
            "type": "string",
            "description": "整體財務評級，例如 A、B、C、D"
        },
        "summary": {
            "type": "string",
            "description": "整體財務評語，100 字以內"
        },
        "risks": {
            "type": "array",
            "description": "主要財務風險，固定三項",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "風險標題"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "風險嚴重程度"
                    },
                    "reason": {
                        "type": "string",
                        "description": "為什麼這是風險"
                    }
                },
                "required": ["title", "severity", "reason"]
            }
        },
        "actions": {
            "type": "array",
            "description": "優先行動建議，固定五項",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "priority": {
                        "type": "integer",
                        "description": "優先順序，1 代表最優先",
                        "minimum": 1,
                        "maximum": 5
                    },
                    "action": {
                        "type": "string",
                        "description": "具體行動"
                    },
                    "target": {
                        "type": "string",
                        "description": "這個行動要達成的目標"
                    }
                },
                "required": ["priority", "action", "target"]
            }
        },
        "next_12_months": {
            "type": "array",
            "description": "未來 12 個月策略，固定六項",
            "minItems": 6,
            "maxItems": 6,
            "items": {
                "type": "string"
            }
        },
        "one_sentence_summary": {
            "type": "string",
            "description": "一句話總結"
        }
    },
    "required": [
        "overall_rating",
        "summary",
        "risks",
        "actions",
        "next_12_months",
        "one_sentence_summary"
    ]
}


if privacy_mode:
    st.warning("隱私模式開啟時不會送出資料給 GPT。請關閉隱私模式後再產生分析。")
else:
    if st.button("產生 GPT 結構化財務分析"):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

            prompt = f"""
你是一位謹慎、務實、保守的個人財務顧問。

重要規則：
- 不要推薦具體個股。
- 不要承諾或保證投資報酬。
- 不要給稅務、法律、保險合約等專業結論，只能提醒應諮詢專家。
- 優先分析風險、流動性、負債、資產集中度、現金流。
- 建議要具體、可執行、適合普通個人財務管理。
- 使用繁體中文。
- 主要風險固定 3 項。
- 優先行動建議固定 5 項。
- 未來 12 個月策略固定 6 項。
- 請依照指定 JSON schema 回覆。

以下是財務資料：

{financial_summary}
"""

            with st.spinner("GPT 正在分析你的財務資料..."):
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=prompt,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "financial_advice",
                            "schema": ai_schema,
                            "strict": True
                        }
                    }
                )

            raw_text = response.output_text
            ai_result = json.loads(raw_text)

            report_path = Path("data/ai_reports.csv")
            report_path.parent.mkdir(parents=True, exist_ok=True)

            report_row = {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "overall_rating": ai_result["overall_rating"],
                "summary": ai_result["summary"],
                "one_sentence_summary": ai_result["one_sentence_summary"],
                "financial_score": score,
                "rule_grade": grade,
                "total_assets": total_assets,
                "total_debt": total_debt,
                "net_worth": net_worth,
                "cash_ratio": cash_ratio,
                "debt_ratio": debt_ratio,
                "fire_progress": fire_progress,
                "risks_json": json.dumps(ai_result["risks"], ensure_ascii=False),
                "actions_json": json.dumps(ai_result["actions"], ensure_ascii=False),
                "next_12_months_json": json.dumps(ai_result["next_12_months"], ensure_ascii=False),
            }

            report_df = pd.DataFrame([report_row])

            if report_path.exists():
                old_reports = pd.read_csv(report_path)
                report_df = pd.concat([old_reports, report_df], ignore_index=True)

            report_df.to_csv(report_path, index=False, encoding="utf-8-sig")

            webhook_url = st.secrets.get("AI_REPORT_WEBHOOK_URL", "")
            webhook_secret = st.secrets.get("AI_REPORT_WEBHOOK_SECRET", "")

            if webhook_url and webhook_secret:
                payload = report_row.copy()
                payload["secret"] = webhook_secret

                try:
                    webhook_response = requests.post(
                        webhook_url,
                        json=payload,
                        timeout=15
                    )

                    if webhook_response.status_code == 200:
                        try:
                            webhook_result = webhook_response.json()

                            if webhook_result.get("ok"):
                                st.info("本次 GPT 財務報告也已寫入 Google Sheets。")
                            else:
                                st.warning(
                                    f"Google Sheets 寫入失敗：{webhook_result.get('error')}"
                                )

                        except Exception:
                            st.warning(
                                "Google Sheets 有回應，但不是有效 JSON。請確認 Apps Script Web App 部署設定。"
                            )

                    else:
                        st.warning(
                            f"Google Sheets 寫入失敗，HTTP 狀態碼：{webhook_response.status_code}"
                        )

                except Exception as webhook_error:
                    st.warning(f"Google Sheets 寫入失敗：{webhook_error}")

            else:
                st.info("尚未設定 AI_REPORT_WEBHOOK_URL / AI_REPORT_WEBHOOK_SECRET，僅儲存到本機 CSV。")

            st.success("GPT 結構化財務分析完成")
            st.info("本次 GPT 財務報告已儲存到 data/ai_reports.csv")

            st.metric("AI 財務評級", ai_result["overall_rating"])
            st.write(f"### {ai_result['summary']}")

            st.subheader("🚨 主要風險")

            for risk in ai_result["risks"]:
                severity = risk["severity"]

                if severity == "high":
                    st.error(f"**{risk['title']}**：{risk['reason']}")
                elif severity == "medium":
                    st.warning(f"**{risk['title']}**：{risk['reason']}")
                else:
                    st.info(f"**{risk['title']}**：{risk['reason']}")

            st.subheader("🎯 AI 優先行動建議")

            sorted_actions = sorted(
                ai_result["actions"],
                key=lambda x: x["priority"]
            )

            for action in sorted_actions:
                st.write(
                    f"**{action['priority']}. {action['action']}**  \n"
                    f"目標：{action['target']}"
                )

            st.subheader("📅 未來 12 個月策略")

            for i, strategy in enumerate(ai_result["next_12_months"], start=1):
                st.write(f"{i}. {strategy}")

            st.subheader("🧠 一句總結")
            st.info(ai_result["one_sentence_summary"])

            with st.expander("查看 GPT 原始 JSON"):
                st.json(ai_result)

        except KeyError:
            st.error("找不到 OPENAI_API_KEY。請確認 .streamlit/secrets.toml 已正確設定。")

        except json.JSONDecodeError:
            st.error("GPT 回傳內容不是有效 JSON。請再試一次。")
            if "raw_text" in locals():
                st.text(raw_text)

        except Exception as e:
            st.error(f"OpenAI API 呼叫失敗：{e}")

st.subheader("📚 GPT 財務報告歷史")

ai_reports_df = None
report_source = "無資料"

webhook_url = st.secrets.get("AI_REPORT_WEBHOOK_URL", "")
webhook_secret = st.secrets.get("AI_REPORT_WEBHOOK_SECRET", "")

if webhook_url and webhook_secret:
    try:
        response = requests.get(
            webhook_url,
            params={"secret": webhook_secret},
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("ok"):
                reports = result.get("reports", [])
                ai_reports_df = pd.DataFrame(reports)
                report_source = "Google Sheets"
            else:
                st.warning(f"讀取 Google Sheets AI 報告失敗：{result.get('error')}")
        else:
            st.warning(f"讀取 Google Sheets AI 報告失敗，HTTP 狀態碼：{response.status_code}")

    except Exception as e:
        st.warning(f"讀取 Google Sheets AI 報告失敗：{e}")


if ai_reports_df is None:
    ai_report_path = Path("data/ai_reports.csv")

    if ai_report_path.exists():
        ai_reports_df = pd.read_csv(ai_report_path)
        report_source = "本機 / 雲端暫存 CSV"
    else:
        ai_reports_df = pd.DataFrame()
        report_source = "無資料"


st.caption(f"AI 報告資料來源：{report_source}")

if ai_reports_df.empty:
    st.info("目前還沒有 GPT 財務報告紀錄。")

else:
    summary_columns = [
        "created_at",
        "overall_rating",
        "financial_score",
        "rule_grade",
        "net_worth",
        "cash_ratio",
        "debt_ratio",
        "fire_progress",
        "one_sentence_summary",
    ]

    existing_columns = [
        col for col in summary_columns
        if col in ai_reports_df.columns
    ]

    display_reports_df = ai_reports_df[existing_columns].copy()

    if "net_worth" in display_reports_df.columns:
        display_reports_df["net_worth"] = pd.to_numeric(
            display_reports_df["net_worth"],
            errors="coerce"
        ).map(lambda x: f"NT${x:,.0f}" if pd.notna(x) else "")

    if "cash_ratio" in display_reports_df.columns:
        display_reports_df["cash_ratio"] = pd.to_numeric(
            display_reports_df["cash_ratio"],
            errors="coerce"
        ).map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    if "debt_ratio" in display_reports_df.columns:
        display_reports_df["debt_ratio"] = pd.to_numeric(
            display_reports_df["debt_ratio"],
            errors="coerce"
        ).map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    if "fire_progress" in display_reports_df.columns:
        display_reports_df["fire_progress"] = pd.to_numeric(
            display_reports_df["fire_progress"],
            errors="coerce"
        ).map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    st.dataframe(display_reports_df, use_container_width=True)

    csv_download = ai_reports_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="下載 GPT 財務報告 CSV",
        data=csv_download,
        file_name="ai_reports.csv",
        mime="text/csv"
    )

    if report_source == "本機 / 雲端暫存 CSV":
        if st.button("清空 GPT 財務報告歷史"):
            ai_report_path.unlink()
            st.success("GPT 財務報告歷史已清空，請重新整理頁面。")
    elif report_source == "Google Sheets":
        st.info("目前報告歷史來自 Google Sheets。如需刪除紀錄，請到 Google Sheets 的「AI報告歷史」分頁刪除。")