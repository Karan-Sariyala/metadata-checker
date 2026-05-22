from fastapi.testclient import TestClient
from app.main import app
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

client = TestClient(app)
FIXTURES = "tests/fixtures"


def _path(name: str) -> str:
    return os.path.join(FIXTURES, name)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}


def test_analyze_clean_pdf():
    with open(_path("clean.pdf"), "rb") as f:
        resp = client.post("/api/analyze", files={"file": ("clean.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    required = {
        "document_name", "file_type", "metadata_risk_score",
        "metadata_risk_level", "summary", "extracted_metadata",
        "findings", "recommended_action",
    }
    assert required.issubset(body.keys()), f"Missing keys: {required - body.keys()}"
    assert body["metadata_risk_level"] == "Low"
    assert body["metadata_risk_score"] < 31


def test_analyze_impossible_dates_pdf():
    with open(_path("modified_before_created.pdf"), "rb") as f:
        resp = client.post("/api/analyze", files={"file": ("modified_before_created.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    high = [f for f in body["findings"] if f["severity"] == "High"]
    assert len(high) >= 1, f"Expected at least one High finding, got {len(high)}"
    assert body["metadata_risk_score"] > 30, f"Expected score > 30, got {body['metadata_risk_score']}"


def test_analyze_editing_tool_pdf():
    with open(_path("editing_tool.pdf"), "rb") as f:
        resp = client.post("/api/analyze", files={"file": ("editing_tool.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert len(body["findings"]) > 0, "Expected at least one finding"
    for f in body["findings"]:
        assert f["severity"] != "High", f"Unexpected High severity finding: {f['title']}"


def test_analyze_missing_dates_pdf():
    with open(_path("missing_dates.pdf"), "rb") as f:
        resp = client.post("/api/analyze", files={"file": ("missing_dates.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    date_findings = [f for f in body["findings"] if "date" in f["title"].lower() or "missing" in f["title"].lower()]
    assert len(date_findings) >= 1, "Expected at least one date-related finding"
    assert body["metadata_risk_level"] != "High", f"Expected risk level not High, got {body['metadata_risk_level']}"


def test_analyze_multi_revision_pdf():
    with open(_path("multi_revision.pdf"), "rb") as f:
        resp = client.post("/api/analyze", files={"file": ("multi_revision.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    revision = [f for f in body["findings"] if "revision" in f["title"].lower()]
    assert len(revision) >= 1, "Expected at least one revision finding"
    detail = revision[0].get("technical_detail", "")
    assert "%%EOF" in detail or "byte offset" in detail, f"Expected technical_detail mentioning %%EOF or byte offset, got: {detail}"


def test_unsupported_file_type():
    resp = client.post("/api/analyze", files={"file": ("test.txt", b"hello world", "text/plain")})
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    assert "unsupported" in resp.json()["detail"].lower()


def test_pdf_report_download():
    with open(_path("clean.pdf"), "rb") as f:
        resp = client.post("/api/analyze/pdf-report", files={"file": ("clean.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert resp.content[:4] == b"%PDF", f"Expected PDF header, got: {resp.content[:8]}"


def test_sample_endpoint():
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    body = resp.json()
    required = {
        "document_name", "file_type", "metadata_risk_score",
        "metadata_risk_level", "summary", "extracted_metadata",
        "findings", "recommended_action",
    }
    assert required.issubset(body.keys()), f"Missing keys: {required - body.keys()}"
    assert len(body["findings"]) >= 2, f"Expected at least 2 findings, got {len(body['findings'])}"


def test_corrupt_pdf_returns_422():
    resp = client.post("/api/analyze", files={"file": ("fake.pdf", b"this is not a pdf", "application/pdf")})
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text[:200]}"


def test_large_file_handling():
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for i in range(2500):
        c.drawString(72, 500, f"This is page {i + 1} of a large test document.")
        if i % 50 == 0:
            c.drawString(72, 480, "x" * 4000)
        c.showPage()
    c.save()
    buf.seek(0)
    pdf_bytes = buf.read()
    assert len(pdf_bytes) > 1_000_000, f"Expected PDF > 1MB, got {len(pdf_bytes)} bytes"
    buf.seek(0)
    resp = client.post("/api/analyze", files={"file": ("large.pdf", buf, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    pages = body["extracted_metadata"].get("page_count", 0)
    assert pages > 1, f"Expected multiple pages, got {pages}"
