# Google Cloud 驗證設定指南

本專案使用 Google Gen AI SDK 呼叫 Vertex AI 的 Gemini 與 Embedding 模型。在本機開發環境中，建議透過 Google Cloud CLI 建立 Application Default Credentials（ADC），不需要將密碼、access token 或 service account 金鑰寫入專案。

相關程式設定：

- Vertex AI 模式：`vertexai=True`
- Embedding 模型：`gemini-embedding-001`
- 預設區域：`global`
- 本機驗證：Application Default Credentials（ADC）

## 前置需求

開始前應確認：

- 已建立 Google Cloud 專案。
- 專案已啟用計費。
- 登入帳號有權存取該專案。
- 帳號至少具有 Vertex AI User（`roles/aiplatform.user`）權限。

以下範例使用 Project ID `badminton-ai-assistant`。如果實際 Project ID 不同，請替換所有指令中的值。

> Project ID 不一定等於 Google Cloud Console 顯示的專案名稱，請以 Console 中的 Project ID 為準。

## 1. 安裝 Google Cloud CLI

依照 Google 官方文件安裝 Windows 版本：

- [Install the Google Cloud CLI](https://cloud.google.com/sdk/docs/install-sdk)

安裝完成後，關閉並重新開啟 PowerShell，再確認指令可用：

```powershell
gcloud --version
```

若仍顯示無法辨識 `gcloud`，請重新登入 Windows，或確認 Google Cloud CLI 的 `bin` 目錄已加入使用者的 `PATH`。

## 2. 初始化 Google Cloud CLI

```powershell
gcloud init
```

依照畫面指示：

1. 在瀏覽器登入有專案權限的 Google 帳號。
2. 選擇正確的 Google Cloud 專案。

也可以明確設定 Project ID：

```powershell
gcloud config set project badminton-ai-assistant
```

確認目前登入帳號與專案：

```powershell
gcloud auth list
gcloud config get-value project
```

## 3. 建立本機 Application Default Credentials

`gcloud init` 登入的是 Cloud CLI；Python SDK 使用的 ADC 需要另外建立：

```powershell
gcloud auth application-default login
```

瀏覽器開啟後，使用有專案權限的帳號完成授權。

接著設定 ADC 的 quota project：

```powershell
gcloud auth application-default set-quota-project badminton-ai-assistant
```

驗證 ADC 是否能取得 access token：

```powershell
gcloud auth application-default print-access-token
```

若輸出一長串 token，代表 ADC 已建立。請勿將 token 複製到 `.env`、程式碼或 Git。

官方說明：

- [Set up ADC for a local development environment](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment)

## 4. 啟用 Vertex AI API

```powershell
gcloud services enable aiplatform.googleapis.com --project=badminton-ai-assistant
```

如果出現權限不足，需請專案管理員啟用 Vertex AI API，或授予目前帳號啟用服務的權限。

## 5. 設定 IAM 權限

執行專案的人員帳號至少需要 Vertex AI User：

```text
roles/aiplatform.user
```

建議由專案管理員透過 Google Cloud Console 的 IAM 頁面授權。授權應遵循最小權限原則，不建議為了方便直接授予 Owner。

若收到 `403 PermissionDenied`，請確認：

- ADC 登入的是正確帳號。
- 帳號屬於正確專案。
- 帳號具有 Vertex AI 使用權限。
- 權限異動後已等待數分鐘讓設定生效。

## 6. 設定專案 `.env`

在專案根目錄建立 `.env`：

```powershell
Copy-Item .env.example .env
```

確認至少包含：

```dotenv
GOOGLE_CLOUD_PROJECT=badminton-ai-assistant
GOOGLE_CLOUD_LOCATION=global

GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=768
```

資料庫連線也必須正確，否則 embedding 批次腳本無法讀取球拍資料：

```dotenv
DATABASE_URL=postgresql+psycopg://badminton:badminton_password@localhost:5432/badminton
```

`.env` 已由 `.gitignore` 排除，請勿強制提交。

### `GOOGLE_APPLICATION_CREDENTIALS` 注意事項

使用個人帳號搭配 ADC 時，不需要在 `.env` 設定：

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=...
```

若系統環境中已設定此變數，Google SDK 可能優先讀取其指定的 JSON。當該檔案不存在或憑證無效時，請移除錯誤設定後重新開啟 PowerShell：

```powershell
Remove-Item Env:GOOGLE_APPLICATION_CREDENTIALS -ErrorAction SilentlyContinue
```

若它已被設為永久使用者環境變數，也需要至 Windows「環境變數」設定中移除或修正。

## 7. 測試 Vertex AI 連線

在專案根目錄啟用虛擬環境：

```powershell
.\.venv\Scripts\Activate.ps1
```

先執行單次 embedding 測試：

```powershell
python -m scripts.test_embedding
```

測試成功後，再產生所有尚未建立的球拍 embedding：

```powershell
python -m scripts.embed_rackets
```

此腳本只會處理 `embedding IS NULL` 且啟用中的球拍。執行前也需要：

- Docker PostgreSQL 容器已啟動。
- Alembic migration 已更新至最新版本。
- 球拍 seed 資料已建立。

完整執行順序可使用：

```powershell
docker compose up -d
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m scripts.seed_rackets
python -m scripts.test_embedding
python -m scripts.embed_rackets
```

## 常見錯誤

### `gcloud` 無法辨識

Google Cloud CLI 尚未安裝，或安裝路徑尚未加入 `PATH`。完成安裝後請重新開啟 PowerShell。

### `DefaultCredentialsError`

Python SDK 找不到 ADC。執行：

```powershell
gcloud auth application-default login
gcloud auth application-default set-quota-project badminton-ai-assistant
```

### `403 PermissionDenied`

常見原因包括：

- 登入帳號沒有 `roles/aiplatform.user`。
- ADC 使用了另一個 Google 帳號。
- 指定了錯誤的 Project ID。
- 組織政策禁止使用該模型或區域。

需要切換 ADC 帳號時，可重新執行：

```powershell
gcloud auth application-default login
```

### `SERVICE_DISABLED`

Vertex AI API 尚未啟用：

```powershell
gcloud services enable aiplatform.googleapis.com --project=badminton-ai-assistant
```

### `BILLING_DISABLED`

Google Cloud 專案尚未連結有效的計費帳戶。請在 Google Cloud Console 的 Billing 頁面完成設定。

### 找不到專案或 Project ID 無效

查看目前可存取的專案：

```powershell
gcloud projects list
```

然後同步修正 Cloud CLI 與 `.env` 的 Project ID。

### 認證成功，但 `embed_rackets` 仍失敗

請先分開測試：

```powershell
gcloud auth application-default print-access-token
python -m scripts.test_embedding
docker compose ps
alembic current
```

如果單次 embedding 成功，但批次腳本失敗，問題通常位於資料庫連線、資料表版本或特定資料內容，而不是 Google Cloud 驗證。

## CI/CD 與正式環境

`gcloud auth application-default login` 適合個人本機開發，不適合部署環境。CI/CD 或正式環境應優先使用執行平台提供的 service account 與 Workload Identity，避免建立或提交長效 JSON 金鑰。

任何 service account JSON、access token 或其他憑證都不得提交至 Git。
