# 本地 Docker 開發環境建立指南

本文件說明如何在另一台電腦取得專案後，重新建立本地開發環境。

目前專案的執行方式如下：

- Docker Compose 負責執行 PostgreSQL 17 與 pgvector。
- FastAPI、Alembic 和初始化腳本在本機 Python 虛擬環境中執行。
- Docker volume 中的資料不會透過 Git 同步。

## 前置需求

請先安裝：

- Git
- Docker Desktop（須包含 Docker Compose）
- Python 3

在 PowerShell 中確認工具可用：

```powershell
git --version
docker --version
docker compose version
python --version
```

## 首次建立環境

### 1. 取得並進入專案

若尚未 clone：

```powershell
git clone <repository-url>
Set-Location badminton-ai-assistant
```

若專案已存在，只需要同步目前分支：

```powershell
git pull
```

### 2. 建立環境變數檔案

`.env` 不會提交至 Git，因此每台電腦都需要自行建立：

```powershell
Copy-Item .env.example .env
```

編輯 `.env`，至少設定以下內容：

```dotenv
GOOGLE_CLOUD_PROJECT=badminton-ai-assistant
DATABASE_URL=postgresql+psycopg://badminton:badminton_password@localhost:5432/badminton
```

資料庫名稱、帳號及密碼須與 `docker-compose.yml` 的設定一致。

> 請勿將 `.env` 或任何憑證提交至 Git。

### 3. 啟動 Docker 資料庫

先啟動 Docker Desktop，再於專案根目錄執行：

```powershell
docker compose up -d
```

檢查服務狀態：

```powershell
docker compose ps
```

正常情況下，`badminton-postgres` 容器應處於 `Up` 或 `running` 狀態。

若要查看啟動紀錄：

```powershell
docker compose logs postgres
```

### 4. 建立 Python 虛擬環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

若 PowerShell 阻擋虛擬環境啟動腳本，可只針對目前 PowerShell 視窗暫時放寬限制：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 5. 建立或更新資料表

確認資料庫容器已啟動且虛擬環境已啟用，再執行：

```powershell
alembic upgrade head
```

此指令會套用 `alembic/versions` 中尚未執行的 migration。

### 6. 初始化開發資料

新增球拍基礎資料：

```powershell
python -m scripts.seed_rackets
```

如需建立 embedding，請先完成 Google Cloud 驗證與環境設定，再執行：

```powershell
python -m scripts.embed_rackets
```

### 7. 啟動 FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

可使用以下網址驗證：

- Health check：<http://127.0.0.1:8000/health>
- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

## 日常同步後的啟動流程

一般從 GitHub 拉取最新程式碼後，可執行：

```powershell
git pull
docker compose up -d
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

`pip install -r requirements.txt` 會補上新增的套件；`alembic upgrade head` 會套用其他開發者新增的資料庫 migration。

## 停止與重建環境

停止容器但保留資料：

```powershell
docker compose down
```

重新啟動：

```powershell
docker compose up -d
```

強制重新建立容器，但保留資料 volume：

```powershell
docker compose up -d --force-recreate
```

完全刪除本地資料庫並從空白狀態重建：

```powershell
docker compose down -v
docker compose up -d
alembic upgrade head
python -m scripts.seed_rackets
```

> `docker compose down -v` 會刪除本專案的 PostgreSQL volume 與其中所有本地資料。執行前請先確認不需要保留資料，必要時先備份。

## 從另一台電腦搬移資料庫資料

Git 只同步程式碼、migration 和 seed 腳本，不會同步 Docker volume。若 seed 資料不足以還原所需內容，應在來源電腦匯出資料庫。

來源電腦匯出：

```powershell
docker exec badminton-postgres pg_dump -U badminton -d badminton -Fc -f /tmp/badminton.dump
docker cp badminton-postgres:/tmp/badminton.dump .\badminton.dump
```

將 `badminton.dump` 安全地搬到新電腦的專案目錄後，在新電腦還原：

```powershell
docker cp .\badminton.dump badminton-postgres:/tmp/badminton.dump
docker exec badminton-postgres pg_restore -U badminton -d badminton --clean --if-exists /tmp/badminton.dump
```

資料庫 dump 可能包含非公開資料，不應直接提交至 Git。

## 常見問題

### Port 5432 已被占用

代表本機已有 PostgreSQL 或其他容器使用該連接埠。可先查看目前容器：

```powershell
docker ps
```

停止衝突服務，或調整 `docker-compose.yml` 左側的主機 port，例如：

```yaml
ports:
  - "5433:5432"
```

此時 `.env` 也要改用 `localhost:5433`。

### 應用程式顯示 `DATABASE_URL environment variable is not set`

確認：

- 專案根目錄存在 `.env`。
- `.env` 中已設定 `DATABASE_URL`。
- 指令是在專案根目錄執行。

### 無法連線到 PostgreSQL

依序檢查：

```powershell
docker compose ps
docker compose logs postgres
```

也可直接進入 PostgreSQL 驗證：

```powershell
docker exec -it badminton-postgres psql -U badminton -d badminton
```

進入 `psql` 後可輸入 `\q` 離開。

### 修改帳號或密碼後沒有生效

PostgreSQL 的初始化環境變數只在第一次建立空白 volume 時套用。若既有 volume 已初始化，修改 `docker-compose.yml` 不會自動修改資料庫帳密。可選擇在資料庫內修改帳密，或在確認資料不需保留後使用 `docker compose down -v` 重建。
