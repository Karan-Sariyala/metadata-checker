from app.models.schemas import Finding


_CLUSTER_TITLES = {
    "Modified date precedes creation date",
    "XMP and document info date mismatch",
    "Known editing tool in metadata",
}

_SEVERITY_BASE = {"High": 30, "Medium": 15, "Low": 5}

_SUMMARIES = {
    "no_findings": "No suspicious metadata patterns were detected.",
    "Low": (
        "Minor metadata signals were detected. These are common in "
        "normal document handling and do not indicate tampering."
    ),
    "Medium": (
        "The document contains metadata patterns that may indicate "
        "post-creation modification or conversion. These signals should be reviewed, "
        "but they do not confirm tampering."
    ),
    "High": (
        "Multiple metadata indicators suggest this document may have "
        "been edited or processed after its original creation. Independent "
        "verification is recommended before relying on this document."
    ),
}

_ACTIONS = {
    "Low": "No action required. File metadata appears consistent with normal document handling.",
    "Medium": "Review the document manually if it is part of a sensitive or high-value process.",
    "High": "Do not rely on this document without independent verification. Consult additional evidence or the document's issuing party.",
}


class RiskScorer:

    def score(self, findings: list[Finding]) -> tuple[int, str, str, str]:
        scores = []
        cluster_hits = 0

        for f in findings:
            base = _SEVERITY_BASE.get(f.severity, 0)
            weighted = base * f.confidence
            scores.append(weighted)
            if f.title in _CLUSTER_TITLES:
                cluster_hits += 1

        scores.sort(reverse=True)

        total = 0.0
        for index, s in enumerate(scores):
            total += s * (0.8 ** index)

        if cluster_hits >= 2:
            total += 10

        score_int = min(round(total), 100)

        if score_int <= 30:
            level = "Low"
        elif score_int <= 65:
            level = "Medium"
        else:
            level = "High"

        if not findings:
            summary = _SUMMARIES["no_findings"]
        else:
            summary = _SUMMARIES[level]

        action = _ACTIONS[level]

        return score_int, level, summary, action


scorer = RiskScorer()
