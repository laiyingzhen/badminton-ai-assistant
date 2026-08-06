from fastapi import FastAPI

from app.api.v1.recommendations import router as recommendation_router


app = FastAPI(
    title="Badminton AI Gear Assistant",
    description="AI Badminton Gear Recommendation API",
    version="0.1.0",
)


app.include_router(
    recommendation_router,
    prefix="/api/v1",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "badminton-ai-assistant",
    }