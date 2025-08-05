# stock_monitor.py
# ──────────────────────────────────────────────────────────────
# • 抓取美股 1 分鐘盤前／盤後  
# • 自動切換台北 04–08 vs 16–21:30  
# • 技術指標：RSI14、ATR、MA5/20/60（min_periods 寫入）  
# • Pickle 快取保留 tz-aware index  • 完整防呆  
# ──────────────────────────────────────────────────────────────

import concurrent.futures as cf
import datetime, time, warnings
from pathlib import Path
from random import random

import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from tabulate import tabulate
from tenacity import retry, stop_after_attempt, wait_fixed

# ────────── 使用者參數 ──────────
TICKERS    = [
    "NVDA","SOFI","OSCR","GRAB","NBIS","FIG",
    "CLS","CRDO","FI","JCAP","LULU","PLTR",
    "PYPL","SOUN","UNH","QQQ","VOO"
]
MAX_WORKERS = 2                    # 降併發到 2，減少限流
CACHE_DIR   = Path("cache_pickle") # Pickle 快取
CACHE_TTL   = 180                  # 180 秒內不重抓
# ──────────────────────────────

warnings.filterwarnings("ignore", category=FutureWarning)
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# █ 1) 工具：取最後純量 ───────────────────────────
def last_val(series: pd.Series):
    if series.empty:
        return float('nan')
    non_nan = series.dropna()
    if non_nan.empty:
        return float('nan')
    return float(non_nan.iloc[-1])

# █ 2) 抓 1m (Pickle 快取)  
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_1m(sym: str) -> pd.DataFrame:
    fn = CACHE_DIR / f"{sym}.pkl"
    now = time.time()
    # 快取
    if fn.exists() and now - fn.stat().st_mtime < CACHE_TTL:
        try:
            df = pd.read_pickle(fn)
            if isinstance(df.index, pd.MultiIndex):
                df.index = df.index.get_level_values(-1)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.loc[:, ~df.columns.duplicated()]
            df.index = (
                df.index.tz_localize("UTC")
                if df.index.tz is None
                else df.index.tz_convert("UTC")
            ).tz_convert("America/New_York")
            return df
        except:
            pass

    # 重新下載
    time.sleep(random() * 1.2)
    df = yf.download(sym, period="1d", interval="1m",
                     prepost=True, auto_adjust=False,
                     threads=False, progress=False)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    df.index = (
        df.index.tz_localize("UTC")
        if df.index.tz is None
        else df.index.tz_convert("UTC")
    ).tz_convert("America/New_York")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()]

    try:
        df.to_pickle(fn)
    except:
        pass
    return df

# █ 2-b) 備援抓 5m ────────────────────────────────
def fetch_minute_safe(sym: str) -> pd.DataFrame:
    df1 = fetch_1m(sym)
    if not df1.empty:
        return df1
    df5 = yf.download(sym, period="1d", interval="5m",
                      prepost=True, auto_adjust=False,
                      threads=False, progress=False)
    if not isinstance(df5, pd.DataFrame) or df5.empty:
        return pd.DataFrame()
    df5.index = (
        df5.index.tz_localize("UTC")
        if df5.index.tz is None
        else df5.index.tz_convert("UTC")
    ).tz_convert("America/New_York")
    if isinstance(df5.columns, pd.MultiIndex):
        df5.columns = df5.columns.get_level_values(0)
    df5 = df5.loc[:, ~df5.columns.duplicated()]
    return df5

# █ 3) 切割盤前/盤中/盤後 ───────────────────────────
def split_prices(df: pd.DataFrame):
    if "Close" not in df.columns:
        return float('nan'), float('nan'), float('nan')
    s = df["Close"]
    pre   = s.between_time("04:00", "09:29")
    reg   = s.between_time("09:30", "16:00")
    post  = s.between_time("16:00", "20:00")
    return last_val(reg), last_val(pre), last_val(post)

# █ 4) 日線技術指標 ───────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_daily_indic(sym: str):
    h = yf.download(sym, period="60d", interval="1d",
                    auto_adjust=False, threads=False, progress=False)
    if not isinstance(h, pd.DataFrame) or h.empty:
        return [pd.NA]*7
    if isinstance(h.columns, pd.MultiIndex):
        h.columns = h.columns.get_level_values(0)
    h = h.loc[:, ~h.columns.duplicated()]
    if "Close" not in h.columns:
        return [pd.NA]*7
    c = h["Close"]
    # 昨日收盤價
    prev_close = round(float(c.iloc[-2]), 2) if len(c) >= 2 and pd.notna(c.iloc[-2]) else pd.NA
    today_close = float(c.iloc[-1]) if len(c) >= 1 and pd.notna(c.iloc[-1]) else pd.NA
    # 今日漲跌幅
    pct_chg = round((today_close - prev_close) / prev_close * 100, 2) if pd.notna(prev_close) and pd.notna(today_close) and prev_close != 0 else pd.NA
    # RSI fallback 長度
    rsi_len = min(14, max(2, len(c)-1))
    rsi     = ta.rsi(c, length=rsi_len).iloc[-1]
    # ATR 需要至少 2 根 K
    atr     = ta.atr(h["High"], h["Low"], c, length=14 if len(c)>=14 else max(2, len(c)-1)).iloc[-1]
    # MA with min_periods=1
    ma5     = c.rolling(5, min_periods=1).mean().iloc[-1]
    ma20    = c.rolling(20, min_periods=1).mean().iloc[-1]
    ma60    = c.rolling(60, min_periods=1).mean().iloc[-1]
    fmt = lambda x: round(x,2) if pd.notna(x) else pd.NA
    return [
        prev_close, pct_chg,
        round(rsi,1) if pd.notna(rsi) else pd.NA,
        fmt(atr), fmt(ma5), fmt(ma20), fmt(ma60)
    ]

# █ 5) 併發抓所有標的 ───────────────────────────
def gather_all():
    rows, failed = [], []
    with cf.ThreadPoolExecutor(MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_minute_safe, t): t for t in TICKERS}
        for fut in cf.as_completed(futs):
            sym = futs[fut]
            try:
                dfm = fut.result()
                if dfm.empty:
                    failed.append(sym); continue
                close, pre_p, post_p = split_prices(dfm)
                prev_close, pct_chg, rsi, atr, ma5, ma20, ma60 = fetch_daily_indic(sym)
                rows.append({
                    "股票": sym, "收盤價": close,
                    "盤前價": pre_p, "盤後價": post_p,
                    "昨日收盤": prev_close, "今日漲跌幅%": pct_chg,
                    "RSI14": rsi, "ATR": atr,
                    "MA5": ma5, "MA20": ma20, "MA60": ma60
                })
            except Exception as e:
                failed.append(sym)
                print(f"[WARN] {sym} 失敗：{e}")
    return pd.DataFrame(rows), failed

# █ 6) 台北時段判斷與變動% ───────────────────────────
def apply_stage(df):
    tw = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    hr = tw.hour + tw.minute/60
    if 4 <= hr < 8:
        df["變動%"] = (df["盤後價"] - df["收盤價"]) / df["收盤價"] * 100
        A,B,title = "收盤價","盤後價","收盤 vs 盤後 (台北04-08)"
    elif 16 <= hr < 21.5:
        df["變動%"] = (df["盤前價"] - df["收盤價"]) / df["收盤價"] * 100
        A,B,title = "收盤價","盤前價","收盤 vs 盤前 (台北16-21:30)"
    else:
        df["變動%"] = (df["盤後價"] - df["收盤價"]) / df["收盤價"] * 100
        A,B,title = "收盤價","盤後價","收盤 vs 盤後"
    df["變動%"] = df["變動%"].round(2)
    return df, A, B, title, tw

# █ 7) 主流程 ───────────────────────────────────
def main():
    df_raw, lost = gather_all()
    if df_raw.empty:
        print("⚠️ 全部標的下載失敗，請稍後重試")
        return

    df, A, B, title, now_tw = apply_stage(df_raw.sort_values("RSI14"))
    cols = ["股票", A, B, "變動%", "昨日收盤", "今日漲跌幅%", "RSI14", "ATR", "MA5", "MA20", "MA60"]

    print(f"\n台北 {now_tw:%Y-%m-%d %H:%M} | {title}")
    print(tabulate(df[cols], headers=cols, tablefmt="pretty", showindex=False))
    if lost:
        print(f"※ 無資料/失敗：{', '.join(lost)}")

if __name__ == "__main__":
    main()
