import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes.analyze import router as analyze_router
from app.models.schemas import AnalysisReport, ExtractedMetadata, Finding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Metadata Mutation Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = int((time.time() - start) * 1000)
    logger.info(
        "%s %s -> %s [%d ms]",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


app.include_router(analyze_router, prefix="/api", tags=["analyze"])


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/sample", response_model=AnalysisReport)
def sample():
    meta = ExtractedMetadata(
        file_name="invoice_2026_03.pdf",
        file_size_bytes=284_672,
        file_type="application/pdf",
        pdf_version="PDF 1.7",
        created_date="2025-11-14T09:23:00Z",
        modified_date="2026-04-03T14:17:00Z",
        author=None,
        creator="Microsoft Word",
        producer="Smallpdf.com",
        title="Invoice #4421",
        subject="Q1 Payment",
        page_count=3,
        is_encrypted=False,
        xmp_metadata={
            "xmp_create_date": "2025-11-14T09:23:00Z",
            "xmp_modify_date": "2026-04-03T14:17:00Z",
            "xmp_creator_tool": "Microsoft Word",
            "pdf_producer": "Smallpdf.com",
        },
        incremental_updates={
            "has_incremental_updates": True,
            "revision_count": 4,
            "xref_count": 4,
            "revision_positions": [185_000, 210_000, 240_000, 260_000],
            "is_suspicious": True,
        },
    )
    findings = [
        Finding(
            title="Modified date precedes creation date",
            severity="High",
            confidence=0.85,
            explanation="The modification timestamp is earlier than the creation timestamp. This is not physically possible in a normal workflow and may indicate metadata was altered.",
        ),
        Finding(
            title="PDF contains multiple saved revisions",
            severity="High",
            confidence=0.75,
            explanation="This PDF contains 4 revision layers, meaning it was saved multiple times after its original creation.",
            technical_detail="%%EOF markers found at byte offsets: [185000, 210000, 240000, 260000]",
        ),
        Finding(
            title="High revision count detected",
            severity="High",
            confidence=0.8,
            explanation="The document contains 4 incremental updates, which is unusually high for a standard document.",
        ),
        Finding(
            title="Modification significantly after creation",
            severity="Medium",
            confidence=0.6,
            explanation="The document was modified more than 6 months after its recorded creation date.",
        ),
        Finding(
            title="Creator and producer mismatch",
            severity="Low",
            confidence=0.55,
            explanation="The document appears to have been created with one tool and processed or exported with another.",
        ),
        Finding(
            title="Known editing tool in metadata",
            severity="Low",
            confidence=0.5,
            explanation="Metadata references a tool commonly used for document editing or conversion.",
            technical_detail="Detected: smallpdf",
        ),
        Finding(
            title="Author field is empty",
            severity="Low",
            confidence=0.35,
            explanation="No author is recorded in the metadata.",
        ),
    ]
    return AnalysisReport(
        document_name="invoice_2026_03.pdf",
        file_type="application/pdf",
        metadata_risk_score=72,
        metadata_risk_level="High",
        summary="Multiple metadata indicators suggest this document may have been edited or processed after its original creation. Independent verification is recommended before relying on this document.",
        extracted_metadata=meta,
        findings=findings,
        recommended_action="Do not rely on this document without independent verification. Consult additional evidence or the document's issuing party.",
    )


@app.on_event("startup")
async def startup():
    logger.info("Metadata Checker API ready")
