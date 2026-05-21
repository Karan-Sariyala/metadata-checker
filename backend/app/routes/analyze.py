import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extractor
from app.services.checker import check_metadata
from app.services.scorer import score_metadata

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
        issues = check_metadata(metadata)
        scores = score_metadata(metadata, issues)
        return {
            "filename": file.filename,
            "metadata": metadata.model_dump(),
            "issues": issues,
            "scores": scores,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
