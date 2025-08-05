# 安裝：pip install yfinance pandas matplotlib

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. 字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 2. 標的清單
tickers = ["NVDA", "SOFI", "OSCR", "GRAB", "NBIS", "FIG","CLS", "CRDO", "FI", "JCAP", "LULU", "PLTR", "PYPL", "SOFI", "SOUN","UNH","QQQ","VOO"]

# 3. 下載含盤前／盤後的 1 分鐘資料，並轉成美東時區
def fetch_minute(symbol):
    df = yf.download(
        symbol, period="1d", interval="1m",
        prepost=True, auto_adjust=False, progress=False
    )
    return df.tz_convert("America/New_York")

# 4. 從 ET 資料中取 Close（09:30–16:00）、Pre（04:00–09:29）、Post（16:00–20:00）最後一筆
def extract_prices(df):
    pre   = df.between_time("04:00", "09:29")['Close']
    reg   = df.between_time("09:30", "16:00")['Close']
    post  = df.between_time("16:00", "20:00")['Close']
    close = float(reg.iloc[-1])  if not reg.empty  else float('nan')
    pre_p = float(pre.iloc[-1])  if not pre.empty  else float('nan')
    post_p= float(post.iloc[-1]) if not post.empty else float('nan')
    return close, pre_p, post_p

# 5. 抓資料並組 DataFrame
rows = []
for s in tickers:
    df_min = fetch_minute(s)
    close, pre_p, post_p = extract_prices(df_min)
    rows.append({"股票":s, "收盤價":close, "盤前價":pre_p, "盤後價":post_p})
df = pd.DataFrame(rows).round(2)

# 6. 取得「台北時間」小時（含小數）
now_tw = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
hour_tw = now_tw.hour + now_tw.minute/60

# 7. 判斷台北時間：04:00–08:00 為盤後，16:00–21:30 為盤前
if 4 <= hour_tw < 8:
    # 台北 04:00–08:00 → ET 16:00–20:00：比對「收盤 vs 盤後」
    df["盤後變動(%)"] = ((df["盤後價"] - df["收盤價"]) / df["收盤價"] *100).round(2)
    comp = ["收盤價","盤後價"]; title="收盤價 vs 盤後價格"
elif 16 <= hour_tw < 21.5:
    # 台北 16:00–21:30 → ET 04:00–09:30：比對「收盤 vs 盤前」
    df["盤前變動(%)"] = ((df["盤前價"] - df["收盤價"]) / df["收盤價"] *100).round(2)
    comp = ["收盤價","盤前價"]; title="收盤價 vs 盤前價格"
else:
    # 其他時段（盤中或夜晚），按需求選一種或都顯示
    df["盤後變動(%)"] = ((df["盤後價"] - df["收盤價"]) / df["收盤價"] *100).round(2)
    comp = ["收盤價","盤後價"]; title="收盤價 vs 盤後價格"

# 8. 印出並繪圖
print(f"台北時間：{now_tw.strftime('%Y-%m-%d %H:%M')}")

# 美化表格輸出
from tabulate import tabulate
table = df[["股票"] + comp + [c for c in df.columns if "變動" in c]].copy()
table.columns = ["股票代碼", comp[0], comp[1], "變動(%)"]
print(f"\n{'='*30}\n台北時間：{now_tw.strftime('%Y-%m-%d %H:%M')}\n{title}")
print(tabulate(table, headers='keys', tablefmt='pretty', showindex=False))

x = range(len(df))

# 精美化繪圖
import seaborn as sns
plt.figure(figsize=(14, 7))
bar_width = 0.35
sns.set(style="whitegrid", font="Microsoft JhengHei", font_scale=1.2)

# 柱狀圖
plt.bar(x, df[comp[0]], width=bar_width, label=comp[0], color="#4F81BD", edgecolor="black")
plt.bar([i + bar_width for i in x], df[comp[1]], width=bar_width, label=comp[1], color="#F79646", edgecolor="black")

# 標籤與美化
plt.xticks([i + bar_width/2 for i in x], df["股票"], rotation=45, ha="right")
plt.ylabel("價格 (USD)", fontsize=14)
plt.title(title, fontsize=16, fontweight="bold")
plt.legend(fontsize=13, loc="best")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()

# 輸出成圖片檔案
plt.savefig("stock_compare.png", dpi=200)
plt.show()
