import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.extractor import extractor
from app.services.checker import checker as metadata_checker
from app.services.scorer import scorer as risk_scorer
from app.services.report_generator import generator as pdf_generator
from app.models.schemas import AnalysisReport

SUPPORTED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

_MIME_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", "application/pdf"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG", "image/png"),
    (b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
]


def _sniff_mime(content: bytes) -> str | None:
    for signature, mime in _MIME_SIGNATURES:
        if content.startswith(signature):
            return mime
    return None


router = APIRouter()


def _run_analysis(file: UploadFile) -> AnalysisReport:
    content: bytes | None = None
    tmp_path: str | None = None
    try:
        content = file.file.read()

        if len(content) == 0:
            raise HTTPException(status_code=422, detail="File appears to be empty")

        sniffed = _sniff_mime(content)
        if sniffed is not None and sniffed in SUPPORTED_TYPES:
            effective_type = sniffed
        elif file.content_type in SUPPORTED_TYPES:
            effective_type = file.content_type
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '{file.content_type}'. "
                       f"Supported: {', '.join(sorted(SUPPORTED_TYPES))}",
            )

        suffix = os.path.splitext(file.filename or "upload")[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        metadata = extractor.extract(tmp_path, file.filename or "unknown", effective_type)

        if metadata.page_count is not None and metadata.page_count == 0:
            raise HTTPException(
                status_code=422,
                detail="PDF appears to have 0 pages and cannot be analyzed",
            )

        findings = metadata_checker.run_checks(metadata)
        score_int, risk_level, summary, action = risk_scorer.score(findings)

        return AnalysisReport(
            document_name=file.filename or "unknown",
            file_type=effective_type,
            metadata_risk_score=score_int,
            metadata_risk_level=risk_level,
            summary=summary,
            extracted_metadata=metadata,
            findings=findings,
            recommended_action=action,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/analyze", response_model=AnalysisReport)
async def analyze_file(file: UploadFile = File(...)):
    try:
        return _run_analysis(file)
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found after upload")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        if "fitz" in type(e).__module__ or "pymupdf" in type(e).__module__:
            raise HTTPException(status_code=422, detail="File could not be parsed as a supported document type")
        raise HTTPException(status_code=500, detail="Internal analysis error")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal analysis error")


@router.post("/analyze/pdf-report")
async def analyze_pdf_report(file: UploadFile = File(...)):
    try:
        report = _run_analysis(file)
        pdf_bytes = pdf_generator.generate(report)
        safe_name = (file.filename or "report").replace(" ", "_")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename=report_{safe_name}.pdf',
            },
        )
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found after upload")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        if "fitz" in type(e).__module__ or "pymupdf" in type(e).__module__:
            raise HTTPException(status_code=422, detail="File could not be parsed as a supported document type")
        raise HTTPException(status_code=500, detail="Internal analysis error")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal analysis error")
