# AI 羽球裝備助手瀏覽器測試指南

本文件說明如何在 Windows 本機啟動 PostgreSQL、FastAPI 後端與靜態網頁，並使用瀏覽器測試 `badminton_equipment_demo.html` 的球拍查詢、文字推薦、語音推薦及推薦球拍連結。

## 1. 測試範圍

- 前端頁面：`badminton_equipment_demo.html`
- 後端預設網址：`http://127.0.0.1:8000`
- 前端預設網址：`http://127.0.0.1:5500`
- API 文件：`http://127.0.0.1:8000/docs`

本頁面會使用以下 API：

| Method | Endpoint | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 確認 FastAPI 是否啟動 |
| `GET` | `/api/v1/rackets` | 依預算、打法與品牌查詢球拍 |
| `GET` | `/api/v1/rackets/{id}` | 取得 AI 推薦的單一球拍資料 |
| `POST` | `/api/v1/recommendations/rackets/chat` | 文字對話推薦 |
| `POST` | `/api/v1/recommendations/rackets/chat/voice` | 語音對話推薦 |

## 2. 前置需求

請先安裝 Python 3、Docker Desktop、Google Cloud CLI，以及 Chrome 或 Edge 等支援錄音的瀏覽器。文字與語音推薦還需要可使用 Vertex AI 的 Google Cloud 專案與帳號。

以下指令均在專案根目錄執行：

```powershell
Set-Location C:\eSlot\localRepository\badminton-ai-assistant
```

## 3. 首次建立 Python 環境

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

後續重新開啟 PowerShell 時，只需要重新進入專案並啟用虛擬環境：

```powershell
Set-Location C:\eSlot\localRepository\badminton-ai-assistant
.\.venv\Scripts\Activate.ps1
```

## 4. 設定環境變數

如果專案根目錄尚未有 `.env`，先建立：

```powershell
Copy-Item .env.example .env
```

編輯 `.env`，至少確認以下設定：

```dotenv
APP_NAME=AI Badminton Equipment Assistant
APP_VERSION=1.0.0
DEBUG=true

API_V1_PREFIX=/api/v1
RACKET_CANDIDATE_LIMIT=3
VOICE_AUDIO_MAX_BYTES=10485760

GOOGLE_CLOUD_PROJECT=你的-Google-Cloud-Project-ID
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash

EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=768

DATABASE_URL=postgresql+psycopg://badminton:badminton_password@localhost:5432/badminton
```

`DEBUG` 必須是 `true` 或 `false`，不可填入 `release` 等其他文字。不要將包含專案資訊或憑證的 `.env` 提交至 Git。

## 5. 啟動與初始化資料庫

先啟動 Docker Desktop，再執行：

```powershell
docker compose up -d
docker compose ps
```

`badminton-postgres` 應顯示為 `Up` 或 `running`。

首次建立環境或 migration 有更新時，執行：

```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m scripts.seed_rackets
```

## 6. 設定 Google Cloud 與球拍向量

文字及語音聊天推薦都會呼叫 Gemini。先完成 Application Default Credentials 驗證：

```powershell
gcloud auth application-default login
```

Google Cloud 專案必須啟用 Vertex AI API，登入帳號也必須有使用 Vertex AI 的權限。

首次建立球拍資料或球拍 embedding 尚未產生時，執行：

```powershell
python -m scripts.embed_rackets
```

如果只需要測試條件篩選，可以不呼叫 Gemini；文字與語音推薦則需要有效的 Google Cloud 設定及球拍 embedding。

## 7. 啟動後端 API

開啟第一個 PowerShell 視窗：

```powershell
Set-Location C:\eSlot\localRepository\badminton-ai-assistant
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

看到以下訊息代表後端已啟動：

```text
Uvicorn running on http://127.0.0.1:8000
```

瀏覽器開啟健康檢查：

```text
http://127.0.0.1:8000/health
```

預期回應：

```json
{
  "status": "ok"
}
```

也可以開啟 Swagger UI 個別測試 API：

```text
http://127.0.0.1:8000/docs
```

## 8. 啟動前端頁面

另開第二個 PowerShell 視窗：

```powershell
Set-Location C:\eSlot\localRepository\badminton-ai-assistant
python -m http.server 5500
```

瀏覽器開啟：

```text
http://127.0.0.1:5500/badminton_equipment_demo.html
```

請使用 HTTP 靜態伺服器開啟，不要直接雙擊 HTML。直接開啟會使用 `file://`，可能造成跨來源請求及麥克風權限問題。

頁面中的 API Base URL 預設應為：

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

如果後端使用不同主機或連接埠，必須同步修改這項設定。

## 9. 測試條件篩選查詢

在頁面選擇打法「進攻型」、預算「5,000 以下」及品牌「YONEX」。前端應呼叫：

```http
GET /api/v1/rackets?budget=5000&playing_style=offensive&brand=YONEX&page=1&pageSize=100
```

也可以直接在瀏覽器測試：

```text
http://127.0.0.1:8000/api/v1/rackets?budget=5000&playing_style=offensive&brand=YONEX&page=1&pageSize=100
```

成功時會回傳 `data` 球拍陣列及 `pagination` 分頁資料，實際內容依本機資料庫而不同。

## 10. 測試文字推薦

在鵝助手輸入：

```text
我是初學者，喜歡全能型打法，預算 3000 元。
```

按 Enter 或送出按鈕後，前端會呼叫：

```http
POST /api/v1/recommendations/rackets/chat
Content-Type: application/json
```

第一次對話的 request body：

```json
{
  "message": "我是初學者，喜歡全能型打法，預算 3000 元。"
}
```

成功回應會包含 `session_id`。前端會將它保存在 `sessionStorage`，後續訊息會自動帶入：

```json
{
  "message": "我偏好 YONEX。",
  "session_id": "前一次 API 回傳的 UUID"
}
```

後端可能回傳以下狀態：

| status | 說明 |
| --- | --- |
| `collecting` | 條件不足，AI 會繼續詢問 |
| `recommended` | 已找到推薦球拍 |
| `no_match` | 條件完整，但找不到符合球拍 |

按聊天視窗的「重新對話」會清除目前的 `session_id`，下一則訊息會建立新的對話。

## 11. 測試推薦球拍連結

當聊天 API 回傳 `status=recommended` 且包含 `recommendation` 時，AI 訊息上方會顯示推薦球拍名稱超連結。

點擊球拍名稱後，前端應只呼叫單筆查詢 API：

```http
GET /api/v1/rackets/{id}
```

例如推薦球拍 ID 為 `3`：

```text
http://127.0.0.1:8000/api/v1/rackets/3
```

成功時應回傳 HTTP `200` 及該球拍完整資料。前端會使用回傳資料：

- 更新打法、預算和品牌等顯示條件。
- 將推薦球拍更新到頁面的查詢結果。
- 捲動到球拍結果區域。

點擊推薦連結後，不應再自動呼叫帶有 query string 的 `GET /api/v1/rackets?...`。

## 12. 測試語音推薦

建議使用最新版 Chrome 或 Edge：

1. 點擊聊天輸入框旁的麥克風圖示。
2. 瀏覽器詢問麥克風權限時選擇「允許」。
3. 說出球拍需求。
4. 再點一次麥克風圖示停止錄音。
5. 等待語音辨識及 AI 回應。

語音範例：

```text
我是中階進攻型球員，預算五千元，偏好 VICTOR。
```

前端會使用 `multipart/form-data` 呼叫：

```http
POST /api/v1/recommendations/rackets/chat/voice
```

Form Data 包含：

| 欄位 | 說明 |
| --- | --- |
| `audio` | 瀏覽器錄製的音訊檔案 |
| `session_id` | 後續對話才會提供；第一次省略 |

語音 API 回應會比文字 API 多一個 `transcript`，前端會將辨識出的文字顯示成使用者訊息。

錄音功能通常只能在 HTTPS、`localhost` 或 `127.0.0.1` 使用，因此不要以 `file://` 開啟頁面。

## 13. 使用 F12 確認 API

在瀏覽器按 `F12` 開啟開發者工具：

1. 切換到 `Network`。
2. 選擇 `Fetch/XHR`。
3. 操作篩選、文字聊天、語音聊天或推薦連結。
4. 點擊請求查看 `Headers`、`Payload`、`Response` 和 HTTP Status。

正常情況會看到：

```text
GET  /api/v1/rackets
GET  /api/v1/rackets/{id}
POST /api/v1/recommendations/rackets/chat
POST /api/v1/recommendations/rackets/chat/voice
```

測試推薦球拍連結時，應看到：

```text
GET http://127.0.0.1:8000/api/v1/rackets/實際球拍ID
Status Code: 200
```

## 14. 執行後端自動測試

啟用虛擬環境後執行全部測試：

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

個別測試：

```powershell
pytest tests\api\test_rackets.py -q
pytest tests\api\test_recommendations.py -q
pytest tests\api\test_chat_voice.py -q
```

## 15. 常見問題

### 頁面顯示 `Failed to fetch` 或無法連線

依序確認 FastAPI 是否仍在執行、`/health` 是否正常、HTML 中的 `API_BASE_URL` 是否正確，以及 F12 Console 是否顯示 CORS 或 JavaScript 錯誤。

### API 啟動時顯示設定驗證錯誤

確認 `.env` 中：

```dotenv
DEBUG=true
```

`DEBUG` 只能使用 `true` 或 `false`。

### 回傳 422 `VALIDATION_ERROR`

條件查詢 API 僅接受以下固定值：

- `playing_style`：`offensive`、`defensive`、`all_round`
- `brand`：`YONEX`、`VICTOR`、`LI-NING`、`JNICE`
- `budget`：必須大於 `0`
- `page`：必須大於或等於 `1`
- `pageSize`：必須介於 `1` 到 `100`

品牌列舉值區分大小寫，`Yonex` 不合法，必須使用 `YONEX`。

### 回傳 404 `RACKET_NOT_FOUND`

確認 URL 中的球拍 ID 存在，且該筆資料的 `is_active` 為 `true`。

### 回傳 503 `DATABASE_SERVICE_ERROR`

```powershell
docker compose ps
docker compose logs postgres
```

### 回傳 502 `GEMINI_SERVICE_ERROR`

確認 `.env` 中的 Google Cloud 專案正確、專案已啟用 Vertex AI API、已執行 `gcloud auth application-default login`，且登入帳號具有 Vertex AI 權限。

### 聊天找不到推薦候選球拍

```powershell
python -m scripts.seed_rackets
python -m scripts.embed_rackets
```

### 麥克風沒有反應

確認網頁從 `http://127.0.0.1:5500` 開啟、瀏覽器及 Windows 已允許麥克風權限，且沒有其他程式獨占麥克風。

### 修改 HTML 後畫面沒有更新

按 `Ctrl + F5` 強制重新整理。如果仍未更新，可在 F12 Network 勾選 `Disable cache` 後再次重新整理。

## 16. 停止服務

前端與後端的 PowerShell 視窗分別按 `Ctrl + C`。停止 PostgreSQL 容器但保留資料：

```powershell
docker compose down
```
