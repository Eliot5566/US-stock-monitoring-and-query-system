import pandas as pd

import threading
import time
import pandas as pd
from finalSt import gather_all, apply_stage
from flask import Flask, render_template_string

app = Flask(__name__)

# 定時自動抓取快取
def fetch_and_save():
    while True:
        try:
            df_raw, lost = gather_all()
            if not df_raw.empty:
                df, A, B, title, now_tw = apply_stage(df_raw.sort_values("RSI14"))
                df.to_pickle("data_latest.pkl")
                with open("meta_latest.txt", "w", encoding="utf-8") as f:
                    f.write(f"{A}|{B}|{title}|{now_tw}")
        except Exception as e:
            print("定時抓取失敗：", e)
        time.sleep(300)  # 每5分鐘抓一次

# 啟動定時任務（在 web 啟動時自動執行）
threading.Thread(target=fetch_and_save, daemon=True).start()

TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>美股監控查詢</title>
    <style>
        body { font-family: Microsoft JhengHei, Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: right; }
        th { background: #f2f2f2; }
        tr:hover { background: #e6f7ff; }
    </style>
</head>
<body>
    <h2>美股監控查詢</h2>
    <p>台北 {{ now_tw.strftime('%Y-%m-%d %H:%M') }} | {{ title }}</p>
    <table>
        <thead>
            <tr>
            {% for col in cols %}
                <th>{{ col }}</th>
            {% endfor %}
            </tr>
        </thead>
        <tbody>
        {% for row in data %}
            <tr>
            {% for col in cols %}
                <td>{{ row[col] }}</td>
            {% endfor %}
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% if lost %}
    <p style="color:red">※ 無資料/失敗：{{ ', '.join(lost) }}</p>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    try:
        df = pd.read_pickle("data_latest.pkl")
        with open("meta_latest.txt", encoding="utf-8") as f:
            A, B, title, now_tw = f.read().split("|")
        cols = ["股票", A, B, "變動%", "昨日收盤", "今日漲跌幅%", "RSI14", "ATR", "MA5", "MA20", "MA60"]
        data = df[cols].to_dict(orient='records')
        lost = []
        return render_template_string(TEMPLATE, data=data, cols=cols, title=title, now_tw=now_tw, lost=lost)
    except Exception as e:
        return f"<h3>⚠️ 資料讀取失敗：{e}<br>請稍候再試，或等待後台自動更新。</h3>"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
