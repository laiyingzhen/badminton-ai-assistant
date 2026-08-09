##啟動FastAPI
uvicorn app.main:app --reload
python -m uvicorn app.main:app --reload
##API 連線網址
http://127.0.0.1:8000/health
##Swagger UI
http://127.0.0.1:8000/docs
##Open UI
http://127.0.0.1:8000/redoc
##在Powershell設定環境變數，指定GCP上的專案名稱
$env:GOOGLE_CLOUD_PROJECT="badminton-ai-assistant"
##Powershell確認環境變數設定成功
echo $env:GOOGLE_CLOUD_PROJECT
##產生球拍測試資料
python -m scripts.seed_rackets
##現有資料加入向量欄位
python -m scripts.embed_rackets
##連線到docker的pgvector，查資料庫
docker exec -it badminton-postgres psql -U badminton -d badminton
###注意事項
本機測試的話，跑測試程式要開Docker才能執行，PostgreSQL安裝在Docker裡面
# 離開conda環境
conda deactivate
#啟動虛擬環境
.\.venv\Scripts\Activate.ps1