# FastAPI app: CORS, /api/health, all routers mounted as stubs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, analyze, blocklist, demo, guardian, live, report, simulator, stats
from app.config import get_settings

settings = get_settings()
app = FastAPI(title="Scam Shield", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "llm": settings.llm_provider, "telegram": settings.telegram_mode}


for r in (analyze, live, guardian, alerts, report, stats, simulator, demo, blocklist):
    app.include_router(r.router)
