from fastapi import FastAPI
from app.routes.analyze import router as analyze_router

app = FastAPI(title="Metadata Checker")

app.include_router(analyze_router, prefix="/api/analyze", tags=["analyze"])


@app.get("/health")
def health():
    return {"status": "ok"}
