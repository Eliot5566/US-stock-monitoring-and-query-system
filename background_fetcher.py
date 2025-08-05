import time
import pandas as pd
from finalSt import gather_all, apply_stage

def fetch_and_save():
    df_raw, lost = gather_all()
    if df_raw.empty:
        return
    df, A, B, title, now_tw = apply_stage(df_raw.sort_values("RSI14"))
    df.to_pickle("data_latest.pkl")
    with open("meta_latest.txt", "w", encoding="utf-8") as f:
        f.write(f"{A}|{B}|{title}|{now_tw}")

if __name__ == "__main__":
    while True:
        try:
            fetch_and_save()
        except Exception as e:
            print("定時抓取失敗：", e)
        time.sleep(300)  # 每5分鐘抓一次
