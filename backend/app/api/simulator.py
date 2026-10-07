# API router: simulator (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/start")
async def simulator_0():
    return _nyi()

@router.post("/turn")
async def simulator_1():
    return _nyi()
