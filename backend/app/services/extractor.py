import os
import xml.etree.ElementTree as ET
from app.models.schemas import ExtractedMetadata


class MetadataExtractor:

    def extract(self, file_path: str, file_name: str, file_type: str) -> ExtractedMetadata:
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

        doc = fitz.open(file_path)
        meta = doc.metadata or {}

        xmp_text = doc.get_xml_metadata()
        xmp_dict = None
        if xmp_text:
            try:
                root = ET.fromstring(xmp_text)
                xmp_dict = self._xml_to_dict(root)
            except ET.ParseError:
                xmp_dict = {"raw": xmp_text}

        result = ExtractedMetadata(
            file_name=file_name,
            file_size_bytes=os.path.getsize(file_path),
            file_type="application/pdf",
            pdf_version=doc.pdf_version(),
            created_date=meta.get("creationDate"),
            modified_date=meta.get("modDate"),
            author=meta.get("author"),
            creator=meta.get("creator"),
            producer=meta.get("producer"),
            title=meta.get("title"),
            subject=meta.get("subject"),
            page_count=doc.page_count,
            is_encrypted=doc.is_encrypted,
            xmp_metadata=xmp_dict,
            raw_info={k: v for k, v in meta.items() if k not in (
                "author", "title", "subject", "creator", "producer",
                "creationDate", "modDate"
            )},
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
            file_name=file_name,
            file_size_bytes=os.path.getsize(file_path),
            file_type=file_type,
            created_date=created_date,
            modified_date=modified_date,
            author=author,
            creator=creator,
            page_count=1,
            raw_info=raw_exif,
        )

    def _extract_docx(self, file_path: str, file_name: str) -> ExtractedMetadata:
        from docx import Document

        doc = Document(file_path)
        props = doc.core_properties

        page_count_proxy = len(doc.paragraphs)

        return ExtractedMetadata(
            file_name=file_name,
            file_size_bytes=os.path.getsize(file_path),
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            created_date=str(props.created) if props.created else None,
            modified_date=str(props.modified) if props.modified else None,
            author=props.author,
            title=props.title,
            subject=props.subject,
            page_count=page_count_proxy,
            raw_info={
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
            },
        )

    @staticmethod
    def _xml_to_dict(element: ET.Element) -> dict:
        result = {}
        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if len(child):
                result[tag] = MetadataExtractor._xml_to_dict(child)
            else:
                result[tag] = child.text or ""
        return result


extractor = MetadataExtractor()
