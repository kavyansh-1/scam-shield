# API router: report (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/report", tags=["report"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/generate")
async def report_0():
    return _nyi()

@router.get("/{report_id}.pdf")
async def report_1():
    return _nyi()
