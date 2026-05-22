from app.services.checker import checker
from app.models.schemas import ExtractedMetadata


def _clean() -> ExtractedMetadata:
    return ExtractedMetadata(
        file_name="test.pdf",
        file_size_bytes=1000,
        file_type="application/pdf",
        pdf_version="PDF 1.7",
        created_date="2026-01-01T10:00:00",
        modified_date="2026-01-01T10:00:00",
        author="Test Author",
        creator="Test Tool",
        producer="Test Tool",
        title="Test Document",
        subject="",
        page_count=1,
        is_encrypted=False,
        xmp_metadata=None,
        raw_info=None,
        incremental_updates=None,
    )


def test_clean_document_no_findings():
    meta = _clean()
    findings = checker.run_checks(meta)
    assert len(findings) == 0, f"Expected 0 findings, got {len(findings)}: {[f.title for f in findings]}"


def test_missing_created_date():
    meta = _clean()
    meta.created_date = None
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "Missing creation date" in f.title]
    assert len(hits) == 1, f"Expected 1 'Missing creation date' finding, got {len(hits)}"
    assert hits[0].severity == "Low"


def test_modified_before_created():
    meta = _clean()
    meta.created_date = "2026-05-01T10:00:00"
    meta.modified_date = "2026-01-01T10:00:00"
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "precedes" in f.title]
    assert len(hits) == 1, f"Expected 1 finding with 'precedes', got {len(hits)}"
    assert hits[0].severity == "High"
    assert hits[0].confidence >= 0.8


def test_modification_much_later():
    meta = _clean()
    meta.created_date = "2025-01-01T10:00:00"
    meta.modified_date = "2026-05-01T10:00:00"
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "significantly after" in f.title]
    assert len(hits) == 1, f"Expected 1 finding about significant gap, got {len(hits)}"
    assert hits[0].severity == "Medium"


def test_both_dates_missing():
    meta = _clean()
    meta.created_date = None
    meta.modified_date = None
    findings = checker.run_checks(meta)
    both = [f for f in findings if "Both dates missing" in f.title]
    single = [f for f in findings if "Missing creation date" in f.title]
    assert len(both) == 1, f"Expected 'Both dates missing', got {len(both)}"
    assert len(single) == 0, f"Should not also trigger 'Missing creation date' separately, but found {len(single)}"


def test_creator_producer_mismatch():
    meta = _clean()
    meta.creator = "Microsoft Word"
    meta.producer = "Adobe Acrobat"
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "mismatch" in f.title and "creator" in f.title.lower()]
    assert len(hits) >= 1, f"Expected mismatch finding, got none"
    assert hits[0].severity == "Low"


def test_known_editing_tool_smallpdf():
    meta = _clean()
    meta.producer = "Smallpdf.com"
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "Known editing tool" in f.title]
    assert len(hits) == 1, f"Expected editing tool finding, got {len(hits)}"
    assert "Smallpdf" in hits[0].technical_detail or "smallpdf" in hits[0].technical_detail


def test_known_editing_tool_canva():
    meta = _clean()
    meta.creator = "Canva"
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "Known editing tool" in f.title]
    assert len(hits) == 1, f"Expected editing tool finding, got {len(hits)}"


def test_empty_author():
    meta = _clean()
    meta.author = ""
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "Author field is empty" in f.title or "author" in f.title.lower()]
    assert len(hits) >= 1, "Expected author-related finding"
    assert hits[0].severity == "Low"


def test_incremental_updates_medium():
    meta = _clean()
    meta.incremental_updates = {
        "has_incremental_updates": True,
        "revision_count": 2,
        "is_suspicious": False,
        "revision_positions": [1000, 2000],
        "xref_count": 2,
    }
    findings = checker.run_checks(meta)
    hits = [f for f in findings if "multiple saved revisions" in f.title.lower()]
    assert len(hits) == 1, f"Expected revision finding, got {len(hits)}"
    assert hits[0].severity == "Medium"


def test_incremental_updates_high():
    meta = _clean()
    meta.incremental_updates = {
        "has_incremental_updates": True,
        "revision_count": 5,
        "is_suspicious": True,
        "revision_positions": [1000, 2000, 3000, 4000, 5000],
        "xref_count": 5,
    }
    findings = checker.run_checks(meta)
    high_hits = [f for f in findings if f.severity == "High" and ("revision" in f.title.lower() or "revision" in f.title.lower())]
    assert len(high_hits) >= 1, "Expected at least one High severity revision finding"
    for f in high_hits:
        assert f.severity == "High"


def test_no_false_positives_acrobat_alone():
    meta = _clean()
    meta.producer = "Adobe Acrobat"
    findings = checker.run_checks(meta)
    acrobat = [
        f for f in findings
        if "acrobat" in (f.title + (f.technical_detail or "")).lower()
    ]
    for f in acrobat:
        assert f.severity == "Low", f"Acrobat finding should be Low severity, got {f.severity}"
    from app.services.scorer import scorer
    score = scorer.score(findings)
    assert score[0] < 31, f"Expected risk score < 31, got {score[0]}"
