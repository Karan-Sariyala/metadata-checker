from pydantic import BaseModel
from typing import Optional, Literal


class ExtractedMetadata(BaseModel):
    file_name: str
    file_size_bytes: int
    file_type: str
    pdf_version: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    page_count: Optional[int] = None
    is_encrypted: Optional[bool] = None
    xmp_metadata: Optional[dict] = None
    raw_info: Optional[dict] = None


class Finding(BaseModel):
    title: str
    severity: Literal["Low", "Medium", "High"]
    confidence: float
    explanation: str
    technical_detail: Optional[str] = None


class AnalysisReport(BaseModel):
    document_name: str
    file_type: str
    metadata_risk_score: int
    metadata_risk_level: Literal["Low", "Medium", "High"]
    summary: str
    extracted_metadata: ExtractedMetadata
    findings: list[Finding]
    recommended_action: str
