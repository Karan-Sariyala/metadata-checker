import os
from datetime import datetime, timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(FIXTURES, exist_ok=True)

TODAY = datetime.now(timezone.utc)


def _make_pdf(path: str, title="Test Document", author="", creator="", producer="",
              content="", created=None, modified=None):
    tmp = path + ".tmp"
    c = canvas.Canvas(tmp, pagesize=A4)
    c.drawString(72, 500, content)
    c.showPage()
    c.save()

    reader = PdfReader(tmp)
    writer = PdfWriter()
    writer.append(reader)

    meta = {
        "/Title": title,
        "/Author": author,
        "/Creator": creator,
        "/Producer": producer,
    }
    if created:
        meta["/CreationDate"] = created.strftime("D:%Y%m%d%H%M%S+00'00'")
    if modified:
        meta["/ModDate"] = modified.strftime("D:%Y%m%d%H%M%S+00'00'")
    writer.add_metadata(meta)

    with open(path, "wb") as f:
        writer.write(f)

    os.unlink(tmp)


_make_pdf(
    os.path.join(FIXTURES, "clean.pdf"),
    title="Clean Document",
    author="Test Author",
    creator="Microsoft Word",
    producer="Microsoft Word",
    content="This is a clean document with no suspicious metadata.",
    created=TODAY,
    modified=TODAY,
)

_make_pdf(
    os.path.join(FIXTURES, "modified_before_created.pdf"),
    title="Date Anomaly Test",
    author="",
    creator="Microsoft Word",
    producer="Smallpdf.com",
    content="This document has an impossible date order.",
    created=datetime(2026, 5, 1, tzinfo=timezone.utc),
    modified=datetime(2026, 1, 1, tzinfo=timezone.utc),
)

_make_pdf(
    os.path.join(FIXTURES, "editing_tool.pdf"),
    title="Editing Tool Test",
    author="",
    creator="Microsoft Word",
    producer="Smallpdf.com",
    content="This document was processed by an online PDF editor.",
    created=datetime(2025, 1, 1, tzinfo=timezone.utc),
    modified=datetime(2025, 6, 15, tzinfo=timezone.utc),
)

_make_pdf(
    os.path.join(FIXTURES, "missing_dates.pdf"),
    title="No Date Metadata",
    author="",
    creator="Unknown",
    producer="Unknown",
    content="This document has no date metadata.",
)

path = os.path.join(FIXTURES, "multi_revision.pdf")
_make_pdf(
    path,
    title="Multi Revision",
    author="Test Author",
    creator="Microsoft Word",
    producer="Adobe Acrobat Pro",
    content="This document has been saved multiple times.",
    created=TODAY,
    modified=TODAY,
)
with open(path, "ab") as f:
    f.write(b"\n%%EOF\n%%EOF\n")

for name in sorted(os.listdir(FIXTURES)):
    if name.startswith("_"):
        continue
    full = os.path.join(FIXTURES, name)
    size = os.path.getsize(full)
    print(f"{name:45s} {size:>8d} bytes")
