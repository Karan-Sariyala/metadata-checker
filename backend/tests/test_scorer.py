from app.models.schemas import Finding
from app.services.scorer import scorer


def make_finding(severity: str, confidence: float, title: str = "Test finding") -> Finding:
    return Finding(
        title=title,
        severity=severity,
        confidence=confidence,
        explanation="Test",
    )


def test_no_findings_score_zero():
    score, level, summary, action = scorer.score([])
    assert score == 0, f"Expected 0, got {score}"
    assert level == "Low"


def test_single_low_finding_stays_low():
    findings = [make_finding("Low", 0.5)]
    score, level, summary, action = scorer.score(findings)
    assert score < 31, f"Expected score < 31, got {score}"
    assert level == "Low"


def test_single_high_finding():
    findings = [make_finding("High", 0.85)]
    score, level, summary, action = scorer.score(findings)
    assert score > 20, f"Expected score > 20, got {score}"
    assert score <= 100, f"Expected score <= 100, got {score}"


def test_many_weak_signals_dont_become_high():
    findings = [make_finding("Low", 0.3) for _ in range(8)]
    score, level, summary, action = scorer.score(findings)
    assert score < 66, f"Expected score < 66, got {score}"
    assert level != "High", f"Should not reach High with weak signals, got {score}"


def test_score_capped_at_100():
    findings = [make_finding("High", 1.0) for _ in range(5)]
    score, level, summary, action = scorer.score(findings)
    assert score == 100, f"Expected 100, got {score}"


def test_cluster_bonus_applies():
    base = [
        Finding(
            title="Modified date precedes creation date",
            severity="High", confidence=0.85,
            explanation="Test",
        ),
    ]
    clustered = base + [
        Finding(
            title="PDF contains multiple saved revisions",
            severity="Medium", confidence=0.75,
            explanation="Test",
        ),
        Finding(
            title="Known editing tool in metadata",
            severity="Low", confidence=0.5,
            explanation="Test",
        ),
    ]

    base_score, _, _, _ = scorer.score(base)
    cluster_score, _, _, _ = scorer.score(clustered)

    assert cluster_score > base_score, (
        f"Expected cluster score ({cluster_score}) > base score ({base_score})"
    )


def test_risk_levels_correct():
    _, lv, _, _ = scorer.score([])
    assert lv == "Low"

    _, lv, _, _ = scorer.score([make_finding("High", 1.0)])
    assert lv == "Low"

    _, lv, _, _ = scorer.score([
        make_finding("High", 1.0),
        make_finding("Medium", 0.1),
    ])
    assert lv == "Medium"

    _, lv, _, _ = scorer.score([
        make_finding("High", 1.0),
        make_finding("High", 0.8),
        make_finding("High", 0.8),
    ])
    assert lv == "Medium"

    _, lv, _, _ = scorer.score([
        make_finding("High", 1.0) for _ in range(3)
    ])
    assert lv == "High"

    _, lv, _, _ = scorer.score([
        make_finding("High", 1.0) for _ in range(5)
    ])
    assert lv == "High"


def test_recommended_action_language():
    _, _, _, action_low = scorer.score([make_finding("Low", 0.5)])
    assert "No action" in action_low

    _, _, _, action_medium = scorer.score([
        make_finding("High", 1.0),
        make_finding("Low", 0.5),
    ])
    assert "manually" in action_medium

    _, _, _, action_high = scorer.score([
        make_finding("High", 1.0) for _ in range(3)
    ])
    assert "verification" in action_high


def test_routine_findings_discounted_alone():
    findings = [
        make_finding("Low", 0.55, "Creator and producer mismatch"),
        make_finding("Low", 0.5, "Known editing tool in metadata"),
        make_finding("Low", 0.35, "Author field is empty"),
    ]
    score, level, _, _ = scorer.score(findings)
    assert score < 15, f"Expected score < 15, got {score}"
    assert level == "Low"


def test_routine_findings_lifted_with_corroboration():
    findings_alone = [
        make_finding("Low", 0.55, "Creator and producer mismatch"),
    ]
    score_alone = scorer.score(findings_alone)[0]

    findings_corroborated = [
        make_finding("Low", 0.55, "Creator and producer mismatch"),
        make_finding("High", 0.85, "Modified date precedes creation date"),
    ]
    score_corroborated = scorer.score(findings_corroborated)[0]

    assert score_corroborated > score_alone, (
        f"Expected corroborated ({score_corroborated}) > alone ({score_alone})"
    )
