import pandas as pd
from finalSt import gather_all, apply_stage
from flask import Flask, render_template_string

app = Flask(__name__)

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
    df_raw, lost = gather_all()
    if df_raw.empty:
        return '<h3>⚠️ 全部標的下載失敗，請稍後重試</h3>'
    df, A, B, title, now_tw = apply_stage(df_raw.sort_values("RSI14"))
    cols = ["股票", A, B, "變動%", "昨日收盤", "今日漲跌幅%", "RSI14", "ATR", "MA5", "MA20", "MA60"]
    data = df[cols].to_dict(orient='records')
    return render_template_string(TEMPLATE, data=data, cols=cols, title=title, now_tw=now_tw, lost=lost)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
