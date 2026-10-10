import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..core import ApiErr, rate_limit, utcnow
from ..models.db import Report, SessionLocal
from ..models.schemas import ReportGenReq
from ..services.alerts import load_analysis
from ..services.pdf_report import build_pdf

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/generate", dependencies=[Depends(rate_limit)])
async def generate(b: ReportGenReq):
    await load_analysis(b.analysis_id)
    rid = str(uuid.uuid4())
    async with SessionLocal() as s:
        s.add(Report(id=rid, analysis_id=b.analysis_id))
        await s.commit()
    return {"report_id": rid, "pdf_url": f"/api/report/{rid}.pdf"}


@router.get("/{report_id}.pdf")
async def get_pdf(report_id: str):
    async with SessionLocal() as s:
        rep = await s.get(Report, report_id)
    if not rep:
        raise ApiErr(404, "report_not_found", "Report not found.")
    result, raw = await load_analysis(rep.analysis_id)
    pdf = build_pdf(result, rep.id, rep.created_at, raw)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="scam-shield-{rep.id[:8]}.pdf"'})
