import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extractor
from app.services.checker import checker as metadata_checker
from app.services.scorer import scorer as risk_scorer
from app.models.schemas import AnalysisReport

SUPPORTED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

router = APIRouter()


@router.post("/analyze", response_model=AnalysisReport)
async def analyze_file(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Supported: {', '.join(sorted(SUPPORTED_TYPES))}",
        )

    tmp_path = None
    try:
        content = await file.read()
        suffix = os.path.splitext(file.filename or "upload")[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        metadata = extractor.extract(tmp_path, file.filename or "unknown", file.content_type)
        findings = metadata_checker.run_checks(metadata)
        score_int, risk_level, summary, action = risk_scorer.score(findings)

        return AnalysisReport(
            document_name=file.filename or "unknown",
            file_type=file.content_type,
            metadata_risk_score=score_int,
            metadata_risk_level=risk_level,
            summary=summary,
            extracted_metadata=metadata,
            findings=findings,
            recommended_action=action,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
