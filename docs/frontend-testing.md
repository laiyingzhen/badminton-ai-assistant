# AI 羽球裝備助手前端測試指南

本文件說明如何在本機啟動後端 API 與前端測試頁面，並使用瀏覽器測試球拍推薦聊天 API。

## 測試目標

- 前端頁面：`index.html`
- API：`POST /api/v1/recommendations/rackets/chat`
- 後端預設網址：`http://127.0.0.1:8000`
- 前端預設網址：`http://127.0.0.1:5500`

## 前置需求

開始前請確認本機已安裝：

- Python
- 專案所需的 Python 套件
- 專案使用的資料庫及其他相依服務
- 可用的瀏覽器，例如 Chrome、Edge 或 Firefox

以下指令皆在專案根目錄執行：

```text
C:\eSlot\localRepository\badminton-ai-assistant
```

## 1. 啟動後端 API

如有使用 Python 虛擬環境，先啟用虛擬環境：

```powershell
.\.venv\Scripts\Activate.ps1
```

啟動 FastAPI 開發伺服器：

```powershell
python -m uvicorn app.main:app --reload
```

終端機出現以下網址時，表示後端已啟動：

```text
http://127.0.0.1:8000
```

使用瀏覽器開啟健康檢查網址：

```text
http://127.0.0.1:8000/health
```

預期回應：

```json
{
  "status": "ok"
}
```

也可以開啟 Swagger UI 確認 API：

```text
http://127.0.0.1:8000/docs
```

## 2. 啟動前端頁面

另開一個 PowerShell 終端機，進入專案根目錄後執行：

```powershell
python -m http.server 5500
```

使用瀏覽器開啟：

```text
http://127.0.0.1:5500/index.html
```

請使用 HTTP 靜態伺服器開啟頁面，不建議直接雙擊 `index.html`。直接開啟檔案時，瀏覽器會使用 `file://` 來源，可能造成跨來源請求問題。

## 3. 確認 API 網址

頁面中的 API 網址應為：

```text
http://127.0.0.1:8000/api/v1/recommendations/rackets/chat
```

若後端使用不同主機或連接埠，請同步修改頁面上的 API 網址。

## 4. 測試聊天流程

在輸入框輸入需求，例如：

```text
我是中階進攻型球員，預算 5000 元，偏好 YONEX。
```

按下「送出」，或直接按 Enter 送出訊息。Shift + Enter 可以換行。

正常情況下，頁面會顯示：

- AI 回覆訊息
- 目前蒐集到的球拍條件
- 推薦結果（條件完整且有符合的球拍時）
- API 回應狀態
- 可展開查看的原始 JSON

第一次請求不需要提供 `session_id`。前端會保存 API 回傳的 `session_id`，後續請求會自動帶入，以延續同一段對話。

可以使用分段訊息測試條件蒐集流程：

1. `我是中階球員。`
2. `主要是進攻型打法。`
3. `預算大約 5000 元。`
4. `偏好 YONEX。`

按下頁面右上角的「重新對話」會清除目前的 `session_id`，下一則訊息將建立新的聊天工作階段。

## 5. 預期 API 請求格式

第一次對話：

```json
{
  "message": "我是中階進攻型球員，預算 5000 元"
}
```

後續對話：

```json
{
  "message": "我比較喜歡 YONEX",
  "session_id": "API 回傳的 UUID"
}
```

API 回應主要欄位包括：

- `session_id`：聊天工作階段識別碼
- `status`：`collecting`、`recommended` 或 `no_match`
- `message`：AI 回覆內容
- `criteria`：目前已蒐集的條件
- `missing_fields`：尚未取得的條件
- `recommendation`：推薦球拍，尚未完成推薦時為 `null`

## 6. CORS 設定

前端與後端使用不同連接埠，因此瀏覽器會視為不同來源。後端需在 `app/main.py` 設定 CORS。

本機開發建議明確允許前端網址：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

修改 CORS 設定後，請重新啟動後端服務。

## 7. 常見問題

### 頁面顯示「無法連線至 API」

請依序確認：

1. 後端終端機是否仍在執行。
2. `http://127.0.0.1:8000/health` 是否能正常開啟。
3. 頁面上的 API 網址是否正確。
4. 瀏覽器開發者工具的 Console 是否有 CORS 錯誤。
5. 後端終端機是否顯示資料庫、環境變數或外部服務錯誤。

### 出現 CORS 錯誤

確認 `allow_origins` 包含實際使用的前端網址。`localhost` 與 `127.0.0.1` 會被瀏覽器視為不同來源，因此應使用與瀏覽器網址列一致的設定。

### 回傳 422 錯誤

這通常代表請求格式驗證失敗。確認：

- `message` 不是空字串。
- `message` 不超過 2000 個字元。
- `session_id` 是有效 UUID，或第一次請求時不傳送此欄位。

### 回傳 404 `CHAT_SESSION_NOT_FOUND`

目前保存的 `session_id` 在後端找不到。按下「重新對話」清除舊的工作階段，再重新送出訊息。

### 修改 `index.html` 後沒有看到變更

重新整理瀏覽器頁面；若仍顯示舊內容，可使用 `Ctrl + F5` 強制重新載入。

## 8. 停止服務

分別在前端與後端的終端機按下：

```text
Ctrl + C
```

即可停止兩個本機開發伺服器。
