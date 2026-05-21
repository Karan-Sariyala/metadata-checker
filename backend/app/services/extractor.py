from typing import Any


def extract_metadata(filename: str, contents: bytes) -> dict[str, Any]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("pdf",):
        return _extract_pdf(contents)
    elif ext in ("docx",):
        return _extract_docx(contents)
    elif ext in ("jpg", "jpeg", "png", "tiff", "tif"):
        return _extract_image(contents)
    else:
        return {"format": ext, "error": "unsupported format"}


def _extract_pdf(contents: bytes) -> dict[str, Any]:
    try:
        import fitz
        doc = fitz.open(stream=contents, filetype="pdf")
        meta = doc.metadata or {}
        doc.close()
        return {"format": "pdf", **meta}
    except ImportError:
        return _extract_pdf_fallback(contents)


def _extract_pdf_fallback(contents: bytes) -> dict[str, Any]:
    from PyPDF2 import PdfReader
    import io
    reader = PdfReader(io.BytesIO(contents))
    meta = reader.metadata or {}
    return {"format": "pdf", **dict(meta)}


def _extract_docx(contents: bytes) -> dict[str, Any]:
    from docx import Document
    import io
    doc = Document(io.BytesIO(contents))
    props = doc.core_properties
    return {
        "format": "docx",
        "title": props.title,
        "author": props.author,
        "created": str(props.created) if props.created else None,
        "modified": str(props.modified) if props.modified else None,
        "last_modified_by": props.last_modified_by,
    }


def _extract_image(contents: bytes) -> dict[str, Any]:
    import io
    from PIL import Image

    img = Image.open(io.BytesIO(contents))
    exif_data = img.info.get("exif", b"")
    exif = {}
    if exif_data:
        try:
            import piexif
            exif_dict = piexif.load(exif_data)
            for ifd_name in exif_dict:
                if isinstance(exif_dict[ifd_name], dict):
                    for tag, value in exif_dict[ifd_name].items():
                        key = piexif.TAGS.get(ifd_name, {}).get(tag, {}).get("name", str(tag))
                        exif[key] = str(value)
        except Exception:
            exif = {"error": "failed to parse EXIF"}
    return {
        "format": img.format.lower() if img.format else "image",
        "mode": img.mode,
        "size": img.size,
        "exif": exif,
    }
