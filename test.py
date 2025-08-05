# finalSt.py
# ──────────────────────────────────────────────────────────────
# • 抓取美股 1 分鐘盤前／盤後價格
# • 自動切換美東時段：盤前 04:00–09:29 vs 盤後 16:00–20:00
# • 欄位扁平化＆刪除重複 Close
# • Fallback：1m→5m，再 fallback Ticker.info 中的 preMarketPrice/postMarketPrice
# • 繪製收盤 vs 盤前／盤後價格對比圖
# ──────────────────────────────────────────────────────────────

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 2. 標的清單
tickers = ["NVDA", "SOFI", "OSCR", "GRAB", "NBIS", "FIG"]

# 3. 抓取 1 分鐘行情（含盤前／盤後），並扁平化欄位
def fetch_minute_data(sym):
    df = yf.download(
        sym,
        period="1d",
        interval="1m",
        prepost=True,
        auto_adjust=False,
        progress=False
    )
    # 若無法下載或空，直接回空 DF
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    # 轉成美東時區
    if df.index.tz is None:
        df = df.tz_localize("UTC").tz_convert("America/New_York")
    else:
        df = df.tz_convert("America/New_York")

    # 扁平化 MultiIndex 欄位，取第一層
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # 刪除重複欄位
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# 4. 提取最後一筆收盤、盤前、盤後價格，並 fallback
def extract_prices(sym, df):
    if "Close" not in df.columns:
        return float("nan"), float("nan"), float("nan")

    s = df["Close"]
    pre     = s.between_time("04:00", "09:29")   # 盤前
    regular = s.between_time("09:30", "16:00")   # 盤中
    post    = s.between_time("16:00", "20:00")   # 盤後

    def last(x):
        return float(x.iloc[-1]) if not x.empty else float("nan")

    close_p = last(regular)
    pre_p   = last(pre)
    post_p  = last(post)

    # 若仍無資料，使用 Ticker.info 進行 fallback
    info = yf.Ticker(sym).info
    if pd.isna(pre_p):
        pre_p = info.get("preMarketPrice", pre_p)
    if pd.isna(post_p):
        post_p = info.get("postMarketPrice", post_p)

    return close_p, pre_p, post_p

# 5. 依序抓取並組成 DataFrame
records = []
for sym in tickers:
    df_min = fetch_minute_data(sym)
    # 如果 1m 完全沒資料，嘗試抓 5 分鐘
    if df_min.empty:
        df_min = yf.download(
            sym,
            period="1d",
            interval="5m",
            prepost=True,
            auto_adjust=False,
            progress=False
        )
        if isinstance(df_min, pd.DataFrame) and not df_min.empty:
            if df_min.index.tz is None:
                df_min = df_min.tz_localize("UTC").tz_convert("America/New_York")
            else:
                df_min = df_min.tz_convert("America/New_York")
            if isinstance(df_min.columns, pd.MultiIndex):
                df_min.columns = df_min.columns.get_level_values(0)
            df_min = df_min.loc[:, ~df_min.columns.duplicated()]

    close_p, pre_p, post_p = extract_prices(sym, df_min)
    records.append({
        "股票": sym,
        "收盤價": close_p,
        "盤前價": pre_p,
        "盤後價": post_p
    })

df = pd.DataFrame(records).round(2)

# 6. 取得當前美東時間（UTC−4）
now_et = datetime.datetime.now(
    datetime.timezone.utc
).astimezone(
    datetime.timezone(datetime.timedelta(hours=-4))
)
hour = now_et.hour + now_et.minute / 60

# 7. 根據時段選擇比較邏輯
if hour < 9.5:
    df["盤後變動(%)"] = ((df["盤後價"] - df["收盤價"]) / df["收盤價"] * 100).round(2)
    comp = ["收盤價", "盤後價", "盤後變動(%)"]
    title = "收盤價 vs 盤後價格對比"
elif hour >= 16:
    df["盤前變動(%)"] = ((df["盤前價"] - df["收盤價"]) / df["收盤價"] * 100).round(2)
    comp = ["收盤價", "盤前價", "盤前變動(%)"]
    title = "收盤價 vs 盤前價格對比"
else:
    df["盤前變動(%)"] = ((df["盤前價"] - df["收盤價"]) / df["收盤價"] * 100).round(2)
    comp = ["收盤價", "盤前價", "盤前變動(%)"]
    title = "收盤價 vs 盤前價格對比"

# 8. 輸出結果
print(f"當前美東時間：{now_et.strftime('%Y-%m-%d %H:%M')}")
print(df[["股票"] + comp])


