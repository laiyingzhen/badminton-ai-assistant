# AI 羽球裝備助手｜Badminton AI Assistant

以自然語言與語音協助使用者挑選羽球拍，整合 **FastAPI、Vertex AI Gemini、PostgreSQL 與 pgvector**，實作從需求蒐集、商品檢索到推薦理由生成的完整流程。

使用者可以描述「我是初學者，喜歡進攻，預算三千元」，系統會擷取選購條件、追問缺少的資訊，再從資料庫中的球拍產生推薦。專案涵蓋聊天前端、後端 API、對話持久化、向量搜尋與自動化測試。

[快速開始](#快速開始) · [系統架構](#系統架構) · [技術設計](#技術設計) · [API 一覽](#api-一覽) · [測試與驗證](#測試與驗證)

## 專案動機

羽球新手往往能描述自己的打法與預算，卻不熟悉球拍規格，也不容易把需求轉成商品篩選條件。本專案將選購流程設計成多輪對話，讓使用者逐步補齊需求，並透過資料庫檢索提供具體的商品選項。

工程上的核心問題是：如何將自然語言轉成可驗證的條件，並讓生成式 AI 的推薦結果對應到實際存在、符合預算的商品。

## 功能展示

| 功能 | 實作內容 |
| --- | --- |
| 對話式推薦 | 擷取程度、打法、預算與品牌；缺少必要條件時自動追問 |
| 多輪條件調整 | 透過 `session_id` 延續對話，支援修改預算與取消品牌偏好 |
| 語音輸入 | 瀏覽器錄音上傳，由 Gemini 轉錄後接入相同的推薦流程 |
| 向量檢索 | SQL 篩選預算、品牌與啟用狀態，再依 pgvector 餘弦距離排序 |
| 商品查詢 | 提供條件篩選、分頁與單筆球拍詳細資料 API |
| 推薦結果驗證 | 結構化輸出搭配候選 ID 檢查，拒絕候選清單以外的商品 |
| 對話紀錄 | PostgreSQL 保存使用者條件與訊息，提供歷史查詢端點 |
| 展示介面 | HTML、CSS 與 JavaScript 單頁介面，串接文字與語音聊天 API |

### 示範情境

以下為操作流程示意；實際回覆與推薦商品取決於模型輸出及資料庫內容。

1. 輸入「我想買羽球拍，預算三千元」。系統保存預算並追問程度、打法，回傳 `collecting`。
2. 接著輸入「我是初學者，偏好進攻」。條件完整後，系統檢索候選球拍並產生推薦，回傳 `recommended`。
3. 輸入「預算改成五千，不限品牌」。系統更新同一個 session 的條件，重新推薦。
4. 若預算或品牌限制下沒有候選商品，回傳 `no_match`，引導調整條件。

也可使用介面的麥克風按鈕，以語音提出需求。後端會回傳辨識文字與聊天結果。

## 系統架構

```mermaid
flowchart TD
    User[使用者] --> UI[瀏覽器聊天介面]
    UI -->|文字或音訊| API[FastAPI]
    API -->|音訊| Transcribe[Gemini 語音轉文字]
    Transcribe --> Chat[Chat Service]
    API -->|文字| Chat
    Chat <-->|保存條件與訊息| DB[(PostgreSQL + pgvector)]
    Chat --> Extract[Gemini 條件擷取]
    Extract --> Check{必要條件完整？}
    Check -->|否| Guidance[查詢部分條件候選並產生追問]
    Check -->|是| Embedding[Gemini Embedding 查詢向量]
    Embedding --> Search[SQL 條件篩選 + 餘弦距離排序]
    Search <--> DB
    Search --> Candidates{有候選商品？}
    Candidates -->|否| NoMatch[引導調整條件]
    Candidates -->|是| Generate[Gemini 結構化推薦]
    Generate --> Validate[驗證推薦 ID 屬於候選清單]
    Guidance --> Response[保存對話並回傳結果]
    NoMatch --> Response
    Validate --> Response
    Response --> UI
```

目前以本機 API 搭配 Docker PostgreSQL 執行。Cloud Run、Cloud SQL 與 Secret Manager 的部署方向另見 [GCP 目標架構](docs/gcp-cloud-run-architecture.md)，屬於後續部署規劃。

## 技術設計

### 1. 結合明確條件與語意檢索

預算、品牌與商品啟用狀態由 SQL 篩選；程度與打法等需求轉成查詢文字，以向量相似度衡量相關性。這讓價格限制由程式與資料庫落實，語意檢索則負責候選排序。

球拍描述使用 `RETRIEVAL_DOCUMENT` 建立向量，使用者需求使用 `RETRIEVAL_QUERY` 建立向量。目前實作採用 `gemini-embedding-001`、768 維向量與 cosine distance，API 預設取 3 筆候選。

### 2. 將生成結果限制在可驗證的候選集合

推薦採用先檢索、再生成的 RAG 流程：後端將候選商品交給 Gemini，以 JSON Schema 取得 `recommended_racket_id` 與 `reason`，再檢查 ID 是否位於候選清單。回傳的品牌、型號與價格取自候選資料。

這項設計降低推薦不存在商品的風險；推薦理由仍由模型生成，候選驗證並不代表文字敘述已完成事實查核。

### 3. 以明確狀態管理多輪對話

聊天服務將條件蒐集與推薦拆成 `collecting`、`recommended`、`no_match` 三種狀態。程度、打法、預算為必填，品牌為選填；每輪合併新條件後重新判斷是否能推薦。對話處理失敗時執行 rollback，避免保存不完整的當輪更新。

### 4. 分層設計與外部服務隔離

API 層負責請求驗證與 HTTP 回應，Service 層處理推薦與聊天流程，Repository 層封裝資料存取。透過 FastAPI dependency injection 與 mock 替換服務，驗證成功、無候選、輸入錯誤及外部服務失敗等情境。

語音入口另檢查 MIME type、空檔案及上傳大小，預設上限為 10 MiB；轉錄完成後共用文字聊天邏輯。

## 技術棧

| 類別 | 技術 |
| --- | --- |
| 後端 | Python、FastAPI、Uvicorn |
| 生成式 AI | Google Gen AI SDK、Vertex AI、Gemini 2.5 Flash（專案預設） |
| Embedding | Gemini Embedding 001、768 維向量 |
| 資料儲存與搜尋 | PostgreSQL 17、pgvector |
| ORM 與 Migration | SQLAlchemy、Alembic、Psycopg |
| 資料驗證與設定 | Pydantic、pydantic-settings、python-dotenv |
| 前端 | HTML、Tailwind CSS CDN、Vanilla JavaScript、MediaRecorder |
| 本機環境 | Docker Compose、Python venv |
| 測試 | pytest、FastAPI TestClient／HTTPX、unittest.mock |

## 快速開始

以下指令在專案根目錄以 **Windows PowerShell** 執行。

### 1. 準備環境

- Python 3.10 以上（程式使用 `X | None` 型別語法）
- Docker Desktop，含 Docker Compose
- Google Cloud CLI，以及可使用 Vertex AI 的 Google Cloud 專案
- 完成 [Google Cloud 驗證設定](docs/google-cloud-authentication.md)，包含啟用 API、權限與 Application Default Credentials（ADC）

### 2. 安裝相依套件

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. 設定環境變數

初次設定時，複製範例檔：

```powershell
Copy-Item .env.example .env
```

編輯 `.env`，至少填入 Google Cloud Project ID 與資料庫連線：

```dotenv
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg://badminton:badminton_password@localhost:5432/badminton
```

候選數量與語音上限等設定見 [.env.example](.env.example)。資料庫帳密對應本機 Compose 設定；Google Cloud 身分驗證使用 ADC。模型呼叫會使用 Google Cloud 配額並可能產生費用。

### 4. 啟動資料庫並建立示範資料

```powershell
docker compose up -d
python -m alembic upgrade head
python -m scripts.seed_rackets
python -m scripts.embed_rackets
```

請等 PostgreSQL 就緒後再執行 migration。`seed_rackets` 會新增 3 筆示範球拍，初次初始化執行一次即可，重複執行會新增重複資料；`embed_rackets` 會呼叫 Vertex AI，為尚未建立向量的啟用商品產生 embedding。

### 5. 啟動後端與展示介面

```powershell
python -m uvicorn app.main:app --reload
```

另開一個終端機，在專案根目錄啟動靜態伺服器：

```powershell
python -m http.server 5500 --bind 127.0.0.1
```

| 入口 | 網址 |
| --- | --- |
| 聊天展示介面 | <http://127.0.0.1:5500/index.html> |
| Swagger UI | <http://127.0.0.1:8000/docs> |
| ReDoc | <http://127.0.0.1:8000/redoc> |
| API 存活檢查 | <http://127.0.0.1:8000/health> |

前端的 `API_BASE_URL` 預設為 `http://127.0.0.1:8000`。語音輸入需允許瀏覽器使用麥克風，並使用支援錄音功能的瀏覽器；遠端展示需配置 HTTPS。`/health` 僅回報 API 存活狀態，不檢查資料庫或 Vertex AI 連線。

## API 一覽

| Method | Endpoint | 說明 |
| --- | --- | --- |
| `GET` | `/health` | API 存活檢查 |
| `GET` | `/api/v1/rackets` | 依預算、打法與選填品牌查詢球拍，支援分頁 |
| `GET` | `/api/v1/rackets/{racket_id}` | 查詢單筆球拍資料 |
| `POST` | `/api/v1/recommendations/rackets` | 依完整條件取得推薦球拍與理由 |
| `POST` | `/api/v1/recommendations/rackets/chat` | 建立或延續文字對話 |
| `POST` | `/api/v1/recommendations/rackets/chat/voice` | 上傳音訊，取得轉錄文字與對話結果 |
| `GET` | `/api/v1/recommendations/rackets/chat/{session_id}/history` | 查詢對話條件與歷史訊息 |

### 文字聊天範例

在 Swagger UI 的 `POST /api/v1/recommendations/rackets/chat` 送出：

```json
{
  "message": "我是初學者，喜歡進攻，預算三千元"
}
```

第一次請求省略 `session_id`，後續請求帶入回傳的 UUID 即可延續對話：

```json
{
  "session_id": "替換為上一輪回傳的 UUID",
  "message": "預算提高到五千元，不限品牌"
}
```

### 單次推薦範例

在 `POST /api/v1/recommendations/rackets` 送出：

```json
{
  "level": "beginner",
  "playing_style": "offensive",
  "budget": 3000,
  "brand": "YONEX"
}
```

程度支援 `beginner`、`intermediate`、`advanced`；打法支援 `offensive`、`defensive`、`all_round`。品牌可省略，指定時支援 `YONEX`、`VICTOR`、`LI-NING`、`JNICE`；實際可推薦品項取決於已匯入的商品。

語音端點採 `multipart/form-data`，欄位為 `audio` 與選填的 `session_id`。完整串接格式見 [前端 API 文件](docs/frontend-api-integration.md)。

## 測試與驗證

完成套件安裝與 `.env` 設定後，執行自動化測試：

```powershell
python -m pytest tests -q
```

現有測試涵蓋推薦服務、Prompt 建構、語音轉錄服務，以及推薦、商品查詢與語音 API。主要透過 mock 與 dependency override 隔離外部服務，驗證輸入限制、服務呼叫與錯誤回應；測試結果不等同於真實模型推薦品質的評估。

`scripts/test_*.py` 為另行執行的驗證腳本，部分會連線到真實資料庫與 Vertex AI。需要驗證完整環境時，可在完成資料初始化後執行：

```powershell
python -m scripts.test_similarity_search
```

介面操作檢查見 [前端測試指南](docs/frontend-testing.md)。

## 專案結構

```text
badminton-ai-assistant/
├── app/
│   ├── api/             # 路由、依賴注入與例外處理
│   ├── core/            # 環境設定、資料庫連線與 logging
│   ├── domain/          # 推薦規則
│   ├── models/          # 球拍、對話與訊息資料模型
│   ├── repositories/    # 商品檢索與聊天資料存取
│   ├── schemas/         # API 與 AI 結構化輸出模型
│   ├── services/        # 聊天、推薦、Gemini 與 Embedding
│   ├── prompts/         # 推薦 Prompt
│   └── main.py          # FastAPI 入口
├── alembic/             # 資料庫版本遷移
├── docs/                # 架構、環境設定與串接文件
├── scripts/             # 示範資料、向量建立與整合驗證
├── tests/               # 單元與 API 測試
├── index.html           # 聊天展示介面
├── docker-compose.yml   # 本機 PostgreSQL / pgvector
├── .env.example         # 環境變數範本
└── requirements.txt     # Python 相依套件
```

## 目前範圍與後續規劃

目前版本提供可在本機執行的推薦流程，內附 3 筆示範商品。價格與規格來自匯入資料，尚未串接即時商品目錄，也尚未建立推薦準確率、延遲與成本的量化評估。

- [ ] 擴充商品資料與更新流程，建立固定的推薦評估案例。
- [ ] 補齊多輪條件合併與真實資料庫整合測試，加入 CI。
- [ ] 記錄模型呼叫延遲、token 使用量與每次推薦成本。
- [ ] 依目標架構完成 Cloud Run／Cloud SQL 部署與自動化交付。
- [ ] 在公開部署前加入使用者驗證、對話存取控制、速率限制及 CORS 設定。

## 相關文件

- [本機 Docker 設定](docs/local-docker-setup.md)
- [Google Cloud 驗證](docs/google-cloud-authentication.md)
- [前端 API 串接](docs/frontend-api-integration.md)
- [前端測試指南](docs/frontend-testing.md)
- [GCP Cloud Run 目標架構](docs/gcp-cloud-run-architecture.md)
