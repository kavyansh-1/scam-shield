# API router: alerts (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/send")
async def alerts_0():
    return _nyi()

@router.get("/{user_id}")
async def alerts_1():
    return _nyi()

@router.post("/{alert_id}/ack")
async def alerts_2():
    return _nyi()
