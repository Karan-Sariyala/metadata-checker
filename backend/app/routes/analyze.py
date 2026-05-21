import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extractor
from app.services.checker import checker as metadata_checker
from app.services.scorer import scorer as risk_scorer

router = APIRouter()


@router.post("/")
async def analyze_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        suffix = os.path.splitext(file.filename or "upload")[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        metadata = extractor.extract(tmp_path, file.filename or "unknown", file.content_type or "application/octet-stream")
        findings = metadata_checker.run_checks(metadata)
        score_int, risk_level, summary, action = risk_scorer.score(findings)
        return {
            "filename": file.filename,
            "metadata": metadata.model_dump(),
            "findings": [f.model_dump() for f in findings],
            "metadata_risk_score": score_int,
            "metadata_risk_level": risk_level,
            "summary": summary,
            "recommended_action": action,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
