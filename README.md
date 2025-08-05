# 美股監控查詢系統

本專案可即時查詢美股 1 分鐘盤前/盤後/收盤價、技術指標（RSI14、ATR、MA5/20/60）、昨日收盤、今日漲跌幅等，並動態生成網頁查詢頁面。

## 功能特色

- 支援美股多標的（可自訂 TICKERS）
- 自動切換台北時區盤前/盤後/收盤
- 技術指標：RSI14、ATR、MA5/20/60
- 昨日收盤、今日漲跌幅
- Pickle 快取，減少 API 請求
- 完整防呆、異常處理
- Flask 動態網頁查詢

## 快速啟動

1. 安裝依賴

   ```
   pip install -r requirements.txt
   ```

2. 執行查詢網頁

   ```
   python stock_monitor_web.py
   ```

   或部署到 Render/Heroku，會自動偵測 PORT。

3. 瀏覽器開啟
   [http://localhost:5000](http://localhost:5000)

## 部署到雲端平台

- 需包含 `requirements.txt`、`Procfile`、`.gitignore`。
- 啟動指令：`python stock_monitor_web.py`
- 會自動偵測 PORT（適用 Render/Heroku）。

## 目錄結構

```
finalSt.py           # 主資料抓取與指標計算
stock_monitor_web.py # Flask 查詢頁面
requirements.txt     # 依賴套件
Procfile             # 雲端啟動指令
.gitignore           # 忽略快取與 pyc
cache_pickle/        # 快取資料夾
```

## 注意事項

- cache_pickle/ 可留空，程式會自動建立。
- 若要自訂股票清單，請編輯 `finalSt.py` 的 TICKERS。
- 若遇 API 限流，請稍後重試。

## 聯絡/建議

如需自訂功能、欄位、前端美化，請聯絡作者或開 issue。
