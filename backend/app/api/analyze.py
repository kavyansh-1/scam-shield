from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..core import ApiErr, rate_limit
from ..detection.pipeline import analyze_text
from ..models.schemas import AnalysisResult, AnalyzeTextReq
from ..services.alerts import save_analysis
from ..services.ocr import analyze_image

router = APIRouter(prefix="/api/analyze", tags=["analyze"], dependencies=[Depends(rate_limit)])
ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp"}


@router.post("/text", response_model=AnalysisResult)
async def analyze_text_ep(body: AnalyzeTextReq):
    result = await analyze_text(body.text, source="text")
    await save_analysis(result, raw_text=body.text if body.save_evidence else None)
    return result


@router.post("/image", response_model=AnalysisResult)
async def analyze_image_ep(file: UploadFile = File(...), save_evidence: bool = Form(False)):
    if (file.content_type or "").lower() not in ALLOWED:
        raise ApiErr(415, "bad_file_type", "Only PNG, JPG or WEBP images are allowed.")
    data = await file.read()
    if len(data) > 6 * 1024 * 1024:
        raise ApiErr(413, "file_too_large", "The image must be 6 MB or smaller.")
    if not data:
        raise ApiErr(422, "empty_file", "The image is empty.")
    result = await analyze_image(data, file.content_type.lower())
    await save_analysis(result, raw_text=result.extracted_text if save_evidence else None)
    return result
