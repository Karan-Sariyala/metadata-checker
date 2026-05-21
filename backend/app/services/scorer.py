from typing import Any


def score_metadata(metadata: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    base = 100
    deductions = {"high": 15, "medium": 8, "low": 3, "info": 0}

    total_deduction = sum(deductions.get(i["severity"], 0) for i in issues)

    fields_with_data = sum(1 for v in metadata.values() if v is not None and v != "" and v != {} and v != [])
    total_fields = max(len(metadata), 1)

    privacy_score = max(0, base - total_deduction)
    completeness_score = round((fields_with_data / total_fields) * 100)

    return {
        "privacy_score": privacy_score,
        "completeness_score": completeness_score,
        "total_issues": len(issues),
        "deductions": total_deduction,
    }
