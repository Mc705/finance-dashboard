# 個人財務 Dashboard

這是一個個人財務管理 Dashboard，使用 Google Sheets 作為資料庫，Streamlit 作為前端介面，並整合 OpenAI GPT 產生結構化財務分析報告。

---

## 功能特色

- 自動讀取 Google Sheets 財務資料
- 顯示核心財務指標
  - 總資產
  - 總負債
  - 淨值
  - 總現金
  - 股票市值
  - 股票損益
  - 負債比
  - 現金比例
- 顯示被動收入
  - 年股息
  - 月被動收入
- 財務健康診斷
  - 財務健康分數
  - 財務評級
  - 主要風險提醒
  - 優先行動建議
- FIRE 財務自由進度
- 未來 1～20 年財富成長預測
- 資產配置圓餅圖
- 淨值歷史趨勢圖
- OpenAI GPT 財務顧問
  - 產生結構化財務分析
  - 分析主要風險
  - 產生行動建議
  - 產生未來 12 個月策略
- GPT 報告寫回 Google Sheets
- GPT 報告歷史查詢與 CSV 下載
- 隱私模式，可隱藏金額

---

## 系統架構

```text
Google Sheets
    ↓
Streamlit Dashboard
    ↓
OpenAI GPT 財務分析
    ↓
Apps Script Webhook
    ↓
Google Sheets AI 報告歷史
```

---

## 使用技術

- Python
- Streamlit
- Pandas
- Plotly
- OpenAI API
- Google Sheets
- Google Apps Script
- GitHub
- Streamlit Cloud

---

## 專案檔案結構

```text
finance-dashboard
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ .streamlit/
│  └─ secrets.toml          # 本機使用，不上傳 GitHub
└─ data/
   ├─ Dashboard.csv         # 本機備援，不上傳 GitHub
   ├─ net_worth_history.csv # 本機備援，不上傳 GitHub
   └─ ai_reports.csv        # 本機暫存，不上傳 GitHub
```

---

## 安裝套件

```bash
pip install -r requirements.txt
```

`requirements.txt` 內容：

```txt
streamlit
pandas
plotly
openai
requests
```

---

## 本機執行

```bash
streamlit run app.py
```

開啟瀏覽器：

```text
http://localhost:8501
```

---

## Secrets 設定

本機請建立：

```text
.streamlit/secrets.toml
```

內容格式：

```toml
OPENAI_API_KEY = "your_openai_api_key"

DASHBOARD_CSV_URL = "your_google_sheets_dashboard_csv_url"
NET_WORTH_HISTORY_CSV_URL = "your_google_sheets_net_worth_history_csv_url"

AI_REPORT_WEBHOOK_URL = "your_apps_script_web_app_url"
AI_REPORT_WEBHOOK_SECRET = "your_apps_script_secret_token"
```

部署到 Streamlit Cloud 時，請到：

```text
Settings → Secrets
```

貼上同樣內容。

---

## Google Sheets 資料表

建議至少建立以下分頁：

```text
Dashboard
淨值歷史
AI報告歷史
```

---

## AI報告歷史欄位

`AI報告歷史` 分頁第一列建議使用以下欄位：

```text
created_at
overall_rating
financial_score
rule_grade
net_worth
cash_ratio
debt_ratio
fire_progress
summary
one_sentence_summary
risks_json
actions_json
next_12_months_json
```

---

## Apps Script Webhook

本專案透過 Google Apps Script Web App 將 GPT 分析報告寫回 Google Sheets。

流程：

```text
Streamlit 產生 GPT 分析
→ POST 到 Apps Script Web App
→ Apps Script 驗證 secret
→ 寫入 Google Sheets「AI報告歷史」
→ Streamlit 再從 Google Sheets 讀取報告歷史
```

注意：

- `AI_REPORT_WEBHOOK_URL` 不要公開
- `AI_REPORT_WEBHOOK_SECRET` 不要公開
- Apps Script 的 `SECRET_TOKEN` 必須和 Streamlit Secrets 裡的 `AI_REPORT_WEBHOOK_SECRET` 一致

---

## 安全注意事項

不要上傳以下檔案：

```text
.streamlit/secrets.toml
data/*.csv
venv/
```

`.gitignore` 建議內容：

```gitignore
# Python
venv/
__pycache__/
*.pyc

# Streamlit secrets
.streamlit/secrets.toml

# Local financial data
data/*.csv

# System files
.DS_Store
Thumbs.db
```

---

## 部署到 Streamlit Cloud

部署步驟：

1. 將專案推上 GitHub
2. 到 Streamlit Cloud 建立新 App
3. 選擇 GitHub Repository
4. Branch 選擇 `main`
5. Main file path 填入：

```text
app.py
```

6. 在 Streamlit Cloud Secrets 貼上：

```toml
OPENAI_API_KEY = "your_openai_api_key"

DASHBOARD_CSV_URL = "your_google_sheets_dashboard_csv_url"
NET_WORTH_HISTORY_CSV_URL = "your_google_sheets_net_worth_history_csv_url"

AI_REPORT_WEBHOOK_URL = "your_apps_script_web_app_url"
AI_REPORT_WEBHOOK_SECRET = "your_apps_script_secret_token"
```

7. 按 Deploy

---

## 目前版本

### v1.0

已完成：

- Google Sheets 自動讀取 Dashboard
- Google Sheets 自動讀取淨值歷史
- Streamlit Cloud 部署
- OpenAI GPT 財務分析
- GPT 結構化 JSON 分析
- GPT 報告寫回 Google Sheets
- GPT 報告歷史從 Google Sheets 讀取
- 報告 CSV 下載
- 財務健康診斷
- FIRE 進度
- 財富成長預測
- 資產配置視覺化
- 隱私模式

---

## 未來可改進方向

- 手機版排版優化
- 加入收入 / 支出紀錄
- 加入每月現金流追蹤
- 加入負債還款計畫
- 加入投資組合再平衡建議
- 加入目標資產配置
- 加入定期自動寄送財務報告
- 加入多使用者登入權限
- 加入資料庫，例如 Supabase 或 PostgreSQL
- 加入更完整的風險評分模型

---

## 免責聲明

本專案僅作為個人財務紀錄、視覺化與輔助分析使用。

GPT 產生的內容不構成投資、理財、稅務或法律建議。

實際財務決策仍應依個人狀況，並視需要諮詢專業人士。

---

## 專案狀態

目前此專案已完成第一個可用版本，可作為個人財務追蹤、財務健康檢查、FIRE 進度觀察，以及 AI 財務分析輔助工具。
