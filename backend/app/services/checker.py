from app.models.schemas import ExtractedMetadata


def check_metadata(metadata: ExtractedMetadata) -> list[dict]:
    issues = []

    if metadata.author:
        issues.append({
            "title": "Author metadata present",
            "severity": "Medium",
            "confidence": 1.0,
            "explanation": "Author metadata is present and may identify the creator.",
        })

    if metadata.creator or metadata.producer:
        issues.append({
            "title": "Creator or producer info embedded",
            "severity": "Low",
            "confidence": 1.0,
            "explanation": "Creator or producer tool info is embedded in the file.",
        })

    if metadata.raw_info:
        raw = metadata.raw_info
        gps_keys = [k for k in raw if "gps" in k.lower()]
        if gps_keys:
            issues.append({
                "title": "GPS location data found",
                "severity": "High",
                "confidence": 1.0,
                "explanation": "GPS location data found in EXIF metadata.",
            })
        if "Make" in raw or "Model" in raw:
            issues.append({
                "title": "Camera make/model found",
                "severity": "Medium",
                "confidence": 1.0,
                "explanation": "Device make or model found in EXIF metadata.",
            })

    if metadata.file_type not in (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        issues.append({
            "title": "Unsupported file format",
            "severity": "Medium",
            "confidence": 1.0,
            "explanation": f"Unsupported file type: {metadata.file_type}",
        })

    return issues
