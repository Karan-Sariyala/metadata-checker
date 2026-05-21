from pydantic import BaseModel
from typing import Any, Optional


class MetadataResponse(BaseModel):
    filename: str
    metadata: dict[str, Any]
    issues: list[dict[str, Any]]
    scores: dict[str, Any]
