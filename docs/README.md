# AI 羽球裝備助手

AI 羽球裝備助手是一個以自然語言協助使用者挑選羽球拍的推薦系統。使用者只要說明自己的程度、打法、預算與品牌偏好，系統便會逐步補齊需求，從資料庫搜尋合適的球拍，再由 Gemini 產生具體且易懂的推薦理由。

本專案包含 FastAPI 後端 API 與可直接在瀏覽器使用的單頁聊天介面，適合用來示範生成式 AI、向量搜尋及傳統條件篩選如何整合成完整的推薦流程。

## 主要功能

- 對話式需求蒐集：從自然語言擷取使用者程度、打法、預算與品牌偏好。
- 多輪對話：透過 `session_id` 保存條件與訊息，並支援查詢歷史紀錄。
- 智慧球拍推薦：先依預算與品牌過濾，再以向量相似度找出候選球拍。
- 結構化 AI 回應：使用 Gemini 的 JSON Schema 輸出，確保推薦結果符合後端資料模型。
- 無符合商品引導：找不到球拍時，提示使用者調整預算或放寬品牌限制。
- RESTful API：提供單次推薦、聊天推薦、歷史紀錄與健康檢查端點。
- 瀏覽器展示介面：根目錄的 `index.html` 可直接連接本機 API 進行對話。

## 推薦流程

```text
使用者輸入自然語言
        ↓
Gemini 擷取程度、打法、預算與品牌
        ↓
資料不足 ──→ 產生追問並保存對話
        ↓ 資料完整
Gemini Embedding 建立查詢向量
        ↓
PostgreSQL 條件過濾 + pgvector 餘弦距離排序
        ↓
Gemini 從候選清單選出球拍並說明理由
        ↓
回傳推薦結果與完整條件
```

## 使用技術

| 類別 | 技術 | 用途 |
| --- | --- | --- |
| 後端框架 | Python、FastAPI、Uvicorn | 建立 API、資料驗證與開發伺服器 |
| AI 模型 | Google Vertex AI、Gemini 2.5 Flash | 條件擷取、對話引導與最終推薦 |
| 向量模型 | Gemini Embedding 001 | 建立 768 維球拍與查詢向量 |
| 資料庫 | PostgreSQL 17 | 儲存球拍、聊天工作階段與訊息 |
| 向量搜尋 | pgvector | 以 cosine distance 搜尋相似球拍 |
| ORM / Migration | SQLAlchemy、Alembic | 資料存取與資料庫版本管理 |
| 資料模型 | Pydantic、pydantic-settings | Request/Response schema 與環境設定 |
| 前端 | HTML、CSS、Vanilla JavaScript | 單頁聊天操作介面 |
| 容器 | Docker Compose | 啟動本機 PostgreSQL/pgvector |
| 測試 | pytest、HTTPX | API 與服務層測試 |

## 專案結構

```text
badminton-ai-assistant/
├── app/
│   ├── api/             # API 路由、依賴注入與錯誤處理
│   ├── core/            # 設定、資料庫連線與 logging
│   ├── models/          # SQLAlchemy 資料模型
│   ├── repositories/    # 球拍與聊天資料存取
│   ├── schemas/         # Pydantic 請求與回應模型
│   ├── services/        # Gemini、Embedding、聊天與推薦流程
│   └── main.py          # FastAPI 應用程式入口
├── alembic/             # 資料庫 migration
├── docs/                # 設定、API 串接與測試文件
├── scripts/             # 測試資料、向量建立與搜尋驗證工具
├── tests/               # 單元測試與 API 測試
├── index.html           # 瀏覽器聊天介面
├── docker-compose.yml   # PostgreSQL/pgvector 服務
└── requirements.txt     # Python 相依套件
```

## 快速開始

### 1. 環境需求

- Python 3
- Docker Desktop（含 Docker Compose）
- Google Cloud 專案與 Vertex AI 使用權限
- 已完成 Google Cloud Application Default Credentials 驗證

Google Cloud 驗證方式請參考 [google-cloud-authentication.md](google-cloud-authentication.md)。

### 2. 建立環境設定

```powershell
Copy-Item .env.example .env
```

確認 `.env` 至少包含以下設定：

```dotenv
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg://badminton:badminton_password@localhost:5432/badminton
```

請勿將含有憑證或敏感資料的 `.env` 提交到 Git。

### 3. 啟動資料庫

```powershell
docker compose up -d
```

### 4. 安裝 Python 套件

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 建立資料表與球拍向量

```powershell
alembic upgrade head
python -m scripts.seed_rackets
python -m scripts.embed_rackets
```

`embed_rackets` 會呼叫 Vertex AI，因此執行前必須完成 Google Cloud 驗證。

### 6. 啟動 API

```powershell
python -m uvicorn app.main:app --reload
```

啟動後可使用：

- Health Check：<http://127.0.0.1:8000/health>
- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

若要使用展示介面，請以瀏覽器或本機靜態伺服器開啟根目錄的 `index.html`，預設會連線至本機聊天 API。

更完整的本機設定說明請參考 [local-docker-setup.md](local-docker-setup.md)。

## API 一覽

| Method | Endpoint | 說明 |
| --- | --- | --- |
| `GET` | `/health` | 檢查 API 是否運作 |
| `POST` | `/api/v1/recommendations/rackets` | 依完整條件取得單次球拍推薦 |
| `POST` | `/api/v1/recommendations/rackets/chat` | 建立或延續對話式推薦 |
| `GET` | `/api/v1/recommendations/rackets/chat/{session_id}/history` | 取得指定對話的條件與訊息紀錄 |

前端資料格式、狀態與錯誤處理請參考 [frontend-api-integration.md](frontend-api-integration.md)。

## 執行測試

```powershell
pytest
```

部分整合測試會使用資料庫或 Google Cloud 服務；執行前請先啟動 Docker 並完成相應的環境設定。

## 設計重點

- AI 不直接回傳任意商品，而是只能從後端查得的候選球拍 ID 中選擇，避免推薦不存在的資料。
- 預算與品牌會先在 SQL 查詢階段過濾，向量距離則負責衡量使用者需求與球拍描述的語意相似度。
- 對話必填條件為打法、程度及預算；品牌為選填，使用者也能在後續訊息中修改或取消品牌偏好。
- 聊天與推薦邏輯集中於 service layer，資料庫操作封裝於 repository layer，方便測試與後續擴充。

## 相關文件

- [本機 Docker 設定](local-docker-setup.md)
- [Google Cloud 驗證](google-cloud-authentication.md)
- [前端 API 串接](frontend-api-integration.md)
- [前端測試指南](frontend-testing.md)

