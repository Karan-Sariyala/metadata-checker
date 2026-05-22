import os
from datetime import datetime
from app.services.extractor import extractor

FIXTURES = "tests/fixtures"


def _path(name: str) -> str:
    return os.path.join(FIXTURES, name)


def test_pdf_fields_extracted():
    meta = extractor.extract(_path("clean.pdf"), "clean.pdf", "application/pdf")
    assert meta.file_name is not None
    assert meta.file_size_bytes is not None and meta.file_size_bytes > 0
    assert meta.file_type == "application/pdf"
    assert meta.page_count is not None


def test_pdf_dates_extracted():
    meta = extractor.extract(_path("editing_tool.pdf"), "editing_tool.pdf", "application/pdf")
    assert meta.created_date is not None, "created_date should not be None"
    assert meta.modified_date is not None, "modified_date should not be None"
    from dateutil import parser as dateparser
    norm_c = checker._normalize_date(meta.created_date) if hasattr(checker, '_normalize_date') else meta.created_date
    norm_m = checker._normalize_date(meta.modified_date) if hasattr(checker, '_normalize_date') else meta.modified_date
    c = dateparser.parse(norm_c)
    m = dateparser.parse(norm_m)
    assert c is not None
    assert m is not None


from app.services.checker import checker


def test_missing_dates_returns_none():
    meta = extractor.extract(_path("missing_dates.pdf"), "missing_dates.pdf", "application/pdf")
    assert meta.created_date is None or meta.created_date.strip() == ""
    assert meta.modified_date is None or meta.modified_date.strip() == ""


def test_incremental_updates_detected():
    meta = extractor.extract(_path("multi_revision.pdf"), "multi_revision.pdf", "application/pdf")
    inc = meta.incremental_updates
    assert inc is not None, "incremental_updates should not be None"
    assert inc["revision_count"] >= 2, f"Expected >= 2, got {inc['revision_count']}"
    assert inc["has_incremental_updates"] is True


def test_clean_no_incremental_updates():
    meta = extractor.extract(_path("clean.pdf"), "clean.pdf", "application/pdf")
    inc = meta.incremental_updates
    assert inc is not None
    assert inc["revision_count"] == 1, f"Expected 1, got {inc['revision_count']}"
    assert inc["has_incremental_updates"] is False


def test_docx_extraction():
    from docx import Document
    tmp = _path("test.docx")
    doc = Document()
    doc.core_properties.author = "Jane Doe"
    doc.core_properties.title = "Test Document"
    doc.add_paragraph("Hello World")
    doc.save(tmp)
    try:
        meta = extractor.extract(tmp, "test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert meta.author == "Jane Doe", f"Expected 'Jane Doe', got {meta.author!r}"
        assert meta.title == "Test Document", f"Expected 'Test Document', got {meta.title!r}"
        assert "wordprocessingml" in meta.file_type
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_jpeg_extraction():
    from PIL import Image
    import piexif
    tmp = _path("test.jpg")
    try:
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}
        exif_bytes = piexif.dump(exif_dict)
        img.save(tmp, exif=exif_bytes)
        img.close()

        meta = extractor.extract(tmp, "test.jpg", "image/jpeg")
        assert meta.file_type == "image/jpeg", f"Expected image/jpeg, got {meta.file_type}"
        assert meta.page_count == 1, f"Expected 1, got {meta.page_count}"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
