from app.models.schemas import ExtractedMetadata, Finding


def score_metadata(metadata: ExtractedMetadata, issues: list[Finding]) -> dict:
    base = 100
    deductions_map = {"High": 15, "Medium": 8, "Low": 3}

    total_deduction = sum(deductions_map.get(i.severity, 0) for i in issues)
    privacy_score = max(0, base - total_deduction)

    return {
        "privacy_score": privacy_score,
        "completeness_score": 0,
        "total_issues": len(issues),
        "deductions": total_deduction,
    }
