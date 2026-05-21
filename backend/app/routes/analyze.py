from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extract_metadata
from app.services.checker import check_metadata
from app.services.scorer import score_metadata

router = APIRouter()


@router.post("/")
async def analyze_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        metadata = extract_metadata(file.filename, contents)
        issues = check_metadata(metadata)
        scores = score_metadata(metadata, issues)
        return {
            "filename": file.filename,
            "metadata": metadata,
            "issues": issues,
            "scores": scores,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
