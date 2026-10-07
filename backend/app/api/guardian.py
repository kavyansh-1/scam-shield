# API router: guardian (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/guardian", tags=["guardian"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/link")
async def guardian_0():
    return _nyi()

@router.get("/{user_id}")
async def guardian_1():
    return _nyi()
