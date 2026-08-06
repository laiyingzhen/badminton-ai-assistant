##啟動FastAPI
uvicorn app.main:app --reload
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

