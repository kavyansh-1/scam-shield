import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import alerts, analyze, blocklist, check, demo, guardian, live, report, simulator, stats
from .config import settings
from .core import ApiErr, cancel_all_tasks
from .llm.base import get_client
from .models.db import init_db
from .services import telegram
from .services.blocklist import seed_blocklist
from .services.purge import purge_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_blocklist()
    bg = [asyncio.create_task(purge_loop()), asyncio.create_task(telegram.poll_loop())]
    yield
    for t in bg:
        t.cancel()
    await asyncio.gather(*bg, return_exceptions=True)
    await cancel_all_tasks()


app = FastAPI(title="Scam Shield API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({settings.FRONTEND_ORIGIN.rstrip("/"), "http://localhost:3000", "http://127.0.0.1:3000"}),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(ApiErr)
async def _api_err(_: Request, e: ApiErr):
    return JSONResponse({"error": e.message, "code": e.code}, status_code=e.status)


@app.exception_handler(RequestValidationError)
async def _val_err(_: Request, e: RequestValidationError):
    first = e.errors()[0] if e.errors() else {}
    loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
    return JSONResponse({"error": f"Invalid input{(' (' + loc + ')') if loc else ''}: {first.get('msg', '')}", "code": "validation_error"}, status_code=422)


@app.exception_handler(StarletteHTTPException)
async def _http_err(_: Request, e: StarletteHTTPException):
    return JSONResponse({"error": str(e.detail), "code": f"http_{e.status_code}"}, status_code=e.status_code)


@app.exception_handler(Exception)
async def _any_err(_: Request, e: Exception):
    logging.getLogger("scamshield").exception("unhandled error")
    return JSONResponse({"error": "Something went wrong on our side.", "code": "internal_error"}, status_code=500)


@app.get("/api/health")
async def health():
    return {"status": "ok", "llm": get_client().name, "telegram": "live" if telegram.is_live() else "mock"}


for r in (analyze.router, check.router, guardian.router, alerts.router, blocklist.router, report.router, stats.router,
          simulator.router, demo.router, live.router):
    app.include_router(r)
