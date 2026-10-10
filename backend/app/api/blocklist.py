from fastapi import APIRouter, Depends

from ..core import rate_limit
from ..models.schemas import BlocklistReportReq
from ..services.blocklist import report_value

router = APIRouter(prefix="/api/blocklist", tags=["blocklist"])


@router.post("/report", dependencies=[Depends(rate_limit)])
async def report(b: BlocklistReportReq):
    return {"value": b.value, "kind": b.kind, "reports": await report_value(b.value, b.kind)}
