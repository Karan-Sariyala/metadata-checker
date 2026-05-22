import os
import re
from app.models.schemas import ExtractedMetadata

_MAX_META_LEN = 500


def _truncate(val: str | None, max_len: int = _MAX_META_LEN) -> str | None:
    if val is None:
        return None
    if len(val) > max_len:
        return val[:max_len] + "...[truncated]"
    return val


def _truncate_dict(d: dict | None, max_len: int = _MAX_META_LEN) -> dict | None:
    if d is None:
        return None
    result = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = _truncate(v, max_len)
        elif isinstance(v, dict):
            result[k] = _truncate_dict(v, max_len)
        elif isinstance(v, list):
            result[k] = [_truncate(x, max_len) if isinstance(x, str) else x for x in v]
        else:
            result[k] = v
    return result


class MetadataExtractor:

    def extract(self, file_path: str, file_name: str, file_type: str) -> ExtractedMetadata:
        if os.path.getsize(file_path) == 0:
            return ExtractedMetadata(
                file_name=file_name,
                file_size_bytes=0,
                file_type=file_type,
                raw_info={"error": "File appears to be empty"},
            )

        if file_type == "application/pdf":
            return self._extract_pdf(file_path, file_name)
        elif file_type in ("image/jpeg", "image/png"):
            return self._extract_image(file_path, file_name, file_type)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_docx(file_path, file_name)
        else:
            return ExtractedMetadata(
                file_name=file_name,
                file_size_bytes=os.path.getsize(file_path),
                file_type=file_type,
                raw_info={"error": "unsupported file type"},
            )

    def _extract_pdf(self, file_path: str, file_name: str) -> ExtractedMetadata:
        import fitz

        enc_result = None
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            if "encrypt" in str(e).lower():
                enc_result = ExtractedMetadata(
                    file_name=file_name,
                    file_size_bytes=os.path.getsize(file_path),
                    file_type="application/pdf",
                    is_encrypted=True,
                    raw_info={"note": "Document is encrypted — limited metadata available"},
                )
            raise
        finally:
            if enc_result is not None:
                return enc_result

        if doc.is_encrypted:
            result = ExtractedMetadata(
                file_name=file_name,
                file_size_bytes=os.path.getsize(file_path),
                file_type="application/pdf",
                page_count=doc.page_count,
                is_encrypted=True,
                raw_info={"note": "Document is encrypted — limited metadata available"},
            )
            doc.close()
            return result

        meta = doc.metadata or {}

        xmp_text = doc.get_xml_metadata()
        xmp_dict = _truncate_dict(self._parse_xmp(xmp_text) if xmp_text else None)

        incremental = self.detect_incremental_updates(file_path)

        result = ExtractedMetadata(
            file_name=_truncate(file_name),
            file_size_bytes=os.path.getsize(file_path),
            file_type="application/pdf",
            pdf_version=meta.get("format"),
            created_date=_truncate(meta.get("creationDate")),
            modified_date=_truncate(meta.get("modDate")),
            author=_truncate(meta.get("author")),
            creator=_truncate(meta.get("creator")),
            producer=_truncate(meta.get("producer")),
            title=_truncate(meta.get("title")),
            subject=_truncate(meta.get("subject")),
            page_count=doc.page_count,
            is_encrypted=doc.is_encrypted,
            xmp_metadata=xmp_dict,
            raw_info={k: _truncate(v) if isinstance(v, str) else v
                      for k, v in meta.items() if k not in (
                          "author", "title", "subject", "creator", "producer",
                          "creationDate", "modDate"
                      )},
            incremental_updates=incremental,
        )
        doc.close()
        return result

    def _extract_image(self, file_path: str, file_name: str, file_type: str) -> ExtractedMetadata:
        from PIL import Image
        import piexif

        img = Image.open(file_path)
        exif_bytes = img.info.get("exif", b"")
        raw_exif = {}
        created_date = None
        modified_date = None
        author = None
        creator = None

        if exif_bytes:
            try:
                exif_dict = piexif.load(exif_bytes)
                for ifd_name in exif_dict:
                    if isinstance(exif_dict[ifd_name], dict):
                        for tag, value in exif_dict[ifd_name].items():
                            tag_name = piexif.TAGS.get(ifd_name, {}).get(tag, {}).get("name", str(tag))
                            raw_exif[tag_name] = str(value)

                ifd0 = exif_dict.get("0th", {})
                if piexif.ImageIFD.DateTime in ifd0:
                    modified_date = ifd0[piexif.ImageIFD.DateTime].decode("utf-8", errors="replace")
                if piexif.ImageIFD.Artist in ifd0:
                    author = ifd0[piexif.ImageIFD.Artist].decode("utf-8", errors="replace")
                make = ifd0.get(piexif.ImageIFD.Make, b"").decode("utf-8", errors="replace")
                model = ifd0.get(piexif.ImageIFD.Model, b"").decode("utf-8", errors="replace")
                if make or model:
                    creator = f"{make} {model}".strip()

                exif_ifd = exif_dict.get("Exif", {})
                if piexif.ExifIFD.DateTimeOriginal in exif_ifd:
                    created_date = exif_ifd[piexif.ExifIFD.DateTimeOriginal].decode("utf-8", errors="replace")

            except Exception as exc:
                raw_exif = {"parse_error": str(exc)}

        img.close()

        return ExtractedMetadata(
            file_name=_truncate(file_name),
            file_size_bytes=os.path.getsize(file_path),
            file_type=file_type,
            created_date=_truncate(created_date),
            modified_date=_truncate(modified_date),
            author=_truncate(author),
            creator=_truncate(creator),
            page_count=1,
            raw_info=_truncate_dict(raw_exif),
        )

    def _extract_docx(self, file_path: str, file_name: str) -> ExtractedMetadata:
        from docx import Document

        doc = Document(file_path)
        props = doc.core_properties

        page_count_proxy = len(doc.paragraphs)

        return ExtractedMetadata(
            file_name=_truncate(file_name),
            file_size_bytes=os.path.getsize(file_path),
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            created_date=_truncate(str(props.created)) if props.created else None,
            modified_date=_truncate(str(props.modified)) if props.modified else None,
            author=_truncate(props.author),
            title=_truncate(props.title),
            subject=_truncate(props.subject),
            page_count=page_count_proxy,
            raw_info=_truncate_dict({
                "paragraph_count": page_count_proxy,
                "page_count_note": "page_count is a proxy based on paragraph count",
                "last_modified_by": props.last_modified_by,
                "revision": props.revision,
                "category": props.category,
                "comments": props.comments,
                "content_status": props.content_status,
                "identifier": props.identifier,
                "language": props.language,
                "version": props.version,
            }),
        )

    def detect_incremental_updates(self, file_path: str) -> dict:
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            eof_positions = []
            search_from = 0
            while True:
                pos = content.find(b"%%EOF", search_from)
                if pos == -1:
                    break
                eof_positions.append(pos)
                search_from = pos + 5

            revision_count = len(eof_positions)
            xref_count = content.count(b"\nxref")

            return {
                "has_incremental_updates": revision_count > 1,
                "revision_count": revision_count,
                "xref_count": xref_count,
                "revision_positions": eof_positions,
                "is_suspicious": revision_count > 2,
            }
        except Exception:
            return {
                "has_incremental_updates": False,
                "revision_count": 1,
                "xref_count": 0,
                "revision_positions": [],
                "is_suspicious": False,
            }

    @staticmethod
    def _parse_xmp(xmp_string: str) -> dict:
        if not xmp_string:
            return {}

        result = {}

        date_patterns = {
            "xmp_create_date": r"xmp:CreateDate[>\s]+([^<\s]+)",
            "xmp_modify_date": r"xmp:ModifyDate[>\s]+([^<\s]+)",
            "dc_date": r"dc:date[>\s]+([^<\s]+)",
            "pdf_creation_date": r"pdf:CreationDate[>\s]+([^<\s]+)",
        }
        for key, pattern in date_patterns.items():
            match = re.search(pattern, xmp_string, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()

        tool_patterns = {
            "xmp_creator_tool": r"xmp:CreatorTool[>\s]+([^<]+)<",
            "pdf_producer": r"pdf:Producer[>\s]+([^<]+)<",
        }
        for key, pattern in tool_patterns.items():
            match = re.search(pattern, xmp_string, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()

        return result


extractor = MetadataExtractor()
