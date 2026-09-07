# 羽球裝備 AI 推薦系統架構

本文件描述使用者從前端提出羽球裝備推薦需求，後端透過 Gemini Embedding、
PostgreSQL/pgvector 向量搜尋與 Gemini 模型產生最終推薦，並部署至 Google Cloud
Run 的目標架構。

## 系統架構圖

```mermaid
flowchart LR
    User[使用者<br/>瀏覽器]

    subgraph GCP[Google Cloud Platform]
        subgraph Run[Cloud Run]
            Frontend[前端<br/>HTML / CSS / JavaScript]
            API[FastAPI API<br/>推薦與對話服務]
            Recommend[Recommendation Service<br/>推薦流程編排]
        end

        subgraph Vertex[Vertex AI]
            Embedding[Gemini Embedding 001<br/>查詢向量化]
            Gemini[Gemini 2.5 Flash<br/>候選評估與推薦理由]
        end

        subgraph Data[資料層]
            CloudSQL[(Cloud SQL for PostgreSQL<br/>球拍資料與對話紀錄)]
            Pgvector[(pgvector<br/>768 維向量與 cosine search)]
        end

        Secret[Secret Manager<br/>資料庫連線等機密設定]
        Logging[Cloud Logging / Monitoring]
    end

    User -->|輸入程度、球風、預算、品牌| Frontend
    Frontend -->|HTTPS POST<br/>/api/v1/recommendations/rackets| API
    API --> Recommend
    Recommend -->|推薦條件文字| Embedding
    Embedding -->|768 維 query embedding| Recommend
    Recommend -->|預算/品牌過濾<br/>cosine distance Top K| Pgvector
    Pgvector --- CloudSQL
    CloudSQL -->|候選裝備與相似度| Recommend
    Recommend -->|使用者條件 + 候選裝備| Gemini
    Gemini -->|結構化推薦 ID 與理由| Recommend
    Recommend --> API
    API -->|JSON 推薦結果| Frontend
    Frontend -->|顯示推薦裝備與原因| User

    Secret -.->|環境變數 / 機密| API
    API -.->|應用程式與錯誤日誌| Logging
```

## 推薦請求時序

```mermaid
sequenceDiagram
    autonumber
    actor U as 使用者
    participant FE as 前端 index.html
    participant API as Cloud Run / FastAPI
    participant EMB as Vertex AI / Gemini Embedding
    participant DB as Cloud SQL / PostgreSQL + pgvector
    participant LLM as Vertex AI / Gemini 2.5 Flash

    U->>FE: 輸入程度、球風、預算與品牌
    FE->>API: POST /api/v1/recommendations/rackets
    API->>API: 驗證請求並組合檢索文字
    API->>EMB: embed_content(RETRIEVAL_QUERY)
    EMB-->>API: 768 維查詢向量
    API->>DB: 條件過濾 + cosine distance Top K
    DB-->>API: 最相似的候選球拍
    API->>LLM: 使用者條件 + 候選清單 + JSON Schema
    LLM-->>API: 推薦球拍 ID + 推薦理由
    API-->>FE: JSON 推薦結果
    FE-->>U: 顯示裝備資訊與推薦原因
```

## GCP 部署流程

```mermaid
flowchart LR
    Dev[開發者 / Git Repository]
    Build[Cloud Build<br/>建置與測試]
    Registry[Artifact Registry<br/>Container Image]
    Deploy[Cloud Run Revision<br/>部署新版本]
    Service[Cloud Run Service<br/>對外 HTTPS URL]
    SA[Service Account<br/>最小權限]
    SQL[(Cloud SQL<br/>PostgreSQL + pgvector)]
    Vertex[Vertex AI<br/>Gemini API]
    Secrets[Secret Manager]

    Dev -->|push / trigger| Build
    Build -->|docker build & push| Registry
    Registry -->|deploy image| Deploy
    Deploy -->|流量切換| Service
    SA -.->|執行身分| Service
    Service -->|Cloud SQL Connector| SQL
    Service -->|Vertex AI API| Vertex
    Service -->|讀取機密| Secrets
```

部署步驟如下：

1. 將 FastAPI 應用與前端靜態檔案封裝為容器映像。
2. Cloud Build 執行測試並建置映像，再推送至 Artifact Registry。
3. 將映像部署為 Cloud Run revision，並設定服務帳戶與必要環境變數。
4. Cloud Run 透過 Cloud SQL Connector 連線至啟用 `pgvector` 的 PostgreSQL。
5. Cloud Run 服務帳戶取得 Vertex AI User、Cloud SQL Client，以及 Secret
   Manager Secret Accessor 等最小必要權限。
6. 驗證 `/health` 後，將流量切換到新 revision；失敗時保留前一 revision
   以便回復。

## 元件與現有程式對照

| 架構元件 | 專案實作 |
| --- | --- |
| 前端推薦表單 | `index.html` |
| FastAPI 入口 | `app/main.py` |
| 推薦 API | `app/api/v1/recommendations.py` |
| 推薦流程編排 | `app/services/recommendation_service.py` |
| Gemini Embedding | `app/services/embedding_service.py` |
| Gemini 結構化推薦 | `app/services/gemini_service.py` |
| pgvector 相似度搜尋 | `app/repositories/racket_repository.py` |
| PostgreSQL 連線 | `app/core/database.py` |
| 資料表 Migration | `alembic/versions/` |

## 主要設定

| 設定 | 建議來源 | 說明 |
| --- | --- | --- |
| `GOOGLE_CLOUD_PROJECT` | Cloud Run 環境變數 | GCP Project ID |
| `GOOGLE_CLOUD_LOCATION` | Cloud Run 環境變數 | Vertex AI 區域，目前預設為 `global` |
| `GEMINI_MODEL` | Cloud Run 環境變數 | 預設 `gemini-2.5-flash` |
| `DATABASE_URL` | Secret Manager | Cloud SQL PostgreSQL 連線資訊 |

正式環境不應將服務帳戶金鑰放入容器。Cloud Run 應直接使用綁定的服務帳戶
取得 Vertex AI、Cloud SQL 與 Secret Manager 的存取權限。
