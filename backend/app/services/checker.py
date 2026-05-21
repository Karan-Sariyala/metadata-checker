from typing import Any


def check_metadata(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    issues = []

    if metadata.get("author"):
        issues.append({
            "field": "author",
            "severity": "medium",
            "message": "Author metadata is present and may identify the creator.",
        })

    if metadata.get("creator") or metadata.get("producer"):
        issues.append({
            "field": "creator",
            "severity": "low",
            "message": "Creator/producer tool info is embedded.",
        })

    if metadata.get("exif") and isinstance(metadata["exif"], dict):
        gps_keys = [k for k in metadata["exif"] if "gps" in k.lower()]
        if gps_keys:
            issues.append({
                "field": "exif.gps",
                "severity": "high",
                "message": "GPS location data found in EXIF metadata.",
            })

        if "Make" in metadata["exif"] or "Model" in metadata["exif"]:
            issues.append({
                "field": "exif.device",
                "severity": "medium",
                "message": "Device make/model found in EXIF metadata.",
            })

    if metadata.get("error") == "unsupported format":
        issues.append({
            "field": "format",
            "severity": "info",
            "message": f"Unsupported file format: {metadata.get('format')}",
        })

    return issues
