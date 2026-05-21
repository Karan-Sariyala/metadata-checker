from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from app.models.schemas import ExtractedMetadata, Finding


_EDIT_TOOLS = [
    "preview", "photoshop", "illustrator", "canva", "smallpdf",
    "ilovepdf", "sejda", "pdf24", "online", "compress", "edit",
]


class MetadataChecker:

    def run_checks(self, metadata: ExtractedMetadata) -> list[Finding]:
        findings: list[Finding] = []
        checks = [
            self._check_missing_creation_date,
            self._check_modified_before_created,
            self._check_modification_significantly_after_creation,
            self._check_both_dates_missing,
            self._check_suspicious_date_format,
            self._check_creator_producer_mismatch,
            self._check_known_editing_tool,
            self._check_author_empty,
            self._check_xmp_date_mismatch,
            self._check_is_encrypted,
            self._check_multiple_saved_revisions,
            self._check_high_revision_count,
            self._check_xmp_creator_tool_mismatch,
        ]
        for check in checks:
            try:
                result = check(metadata)
                if result is not None:
                    findings.append(result)
            except Exception:
                pass
        return findings

    # ── 1 ──────────────────────────────────────────────────────────

    def _check_missing_creation_date(self, metadata: ExtractedMetadata) -> Finding | None:
        if metadata.created_date is None or metadata.created_date.strip() == "":
            return Finding(
                title="Missing creation date",
                severity="Low",
                confidence=0.5,
                explanation=(
                    "No creation date found in metadata. This may be normal for "
                    "scanned or converted documents, but limits verification."
                ),
            )
        return None

    # ── 2 ──────────────────────────────────────────────────────────

    def _check_modified_before_created(self, metadata: ExtractedMetadata) -> Finding | None:
        if not metadata.created_date or not metadata.modified_date:
            return None
        try:
            created = dateparser.parse(metadata.created_date)
            modified = dateparser.parse(metadata.modified_date)
            if modified < created:
                return Finding(
                    title="Modified date precedes creation date",
                    severity="High",
                    confidence=0.85,
                    explanation=(
                        "The modification timestamp is earlier than the creation "
                        "timestamp. This is not physically possible in a normal "
                        "workflow and may indicate metadata was altered."
                    ),
                    technical_detail=f"created={metadata.created_date}, modified={metadata.modified_date}",
                )
        except Exception:
            pass
        return None

    # ── 3 ──────────────────────────────────────────────────────────

    def _check_modification_significantly_after_creation(self, metadata: ExtractedMetadata) -> Finding | None:
        if not metadata.created_date or not metadata.modified_date:
            return None
        try:
            created = dateparser.parse(metadata.created_date)
            modified = dateparser.parse(metadata.modified_date)
            if modified > created and (modified - created).days > 180:
                return Finding(
                    title="Modification significantly after creation",
                    severity="Medium",
                    confidence=0.6,
                    explanation=(
                        "The document was modified more than 6 months after its "
                        "recorded creation date. This may indicate normal editing, "
                        "re-export, or document history worth reviewing."
                    ),
                )
        except Exception:
            pass
        return None

    # ── 4 ──────────────────────────────────────────────────────────

    def _check_both_dates_missing(self, metadata: ExtractedMetadata) -> Finding | None:
        if (metadata.created_date is None or metadata.created_date.strip() == "") and \
           (metadata.modified_date is None or metadata.modified_date.strip() == ""):
            return Finding(
                title="Both dates missing",
                severity="Medium",
                confidence=0.55,
                explanation=(
                    "Neither creation nor modification dates are present. "
                    "This reduces the ability to assess document history."
                ),
            )
        return None

    # ── 5 ──────────────────────────────────────────────────────────

    def _check_suspicious_date_format(self, metadata: ExtractedMetadata) -> Finding | None:
        for val in (metadata.created_date, metadata.modified_date):
            if val and val.strip():
                try:
                    dateparser.parse(val)
                except Exception:
                    return Finding(
                        title="Suspicious date format",
                        severity="Low",
                        confidence=0.45,
                        explanation=(
                            "One or more date fields contain a value that could not "
                            "be parsed as a standard date format."
                        ),
                    )
        return None

    # ── 6 ──────────────────────────────────────────────────────────

    def _check_creator_producer_mismatch(self, metadata: ExtractedMetadata) -> Finding | None:
        if not metadata.creator or not metadata.producer:
            return None
        c = metadata.creator.lower()
        p = metadata.producer.lower()
        if c != p and c not in p and p not in c:
            return Finding(
                title="Creator and producer mismatch",
                severity="Low",
                confidence=0.55,
                explanation=(
                    "The document appears to have been created with one tool "
                    "and processed or exported with another. This is common in "
                    "normal document workflows but is worth noting."
                ),
            )
        return None

    # ── 7 ──────────────────────────────────────────────────────────

    def _check_known_editing_tool(self, metadata: ExtractedMetadata) -> Finding | None:
        detected: list[str] = []
        for field in (metadata.producer, metadata.creator):
            if field:
                lower = field.lower()
                for tool in _EDIT_TOOLS:
                    if tool in lower and tool not in detected:
                        detected.append(tool)
        if not detected:
            return None
        return Finding(
            title="Known editing tool in metadata",
            severity="Low",
            confidence=0.5,
            explanation=(
                "Metadata references a tool commonly used for document "
                "editing or conversion. This alone does not indicate tampering "
                "but may be a signal in combination with other findings."
            ),
            technical_detail=f"Detected: {', '.join(detected)}",
        )

    # ── 8 ──────────────────────────────────────────────────────────

    def _check_author_empty(self, metadata: ExtractedMetadata) -> Finding | None:
        if metadata.author is None or metadata.author.strip() == "":
            return Finding(
                title="Author field is empty",
                severity="Low",
                confidence=0.35,
                explanation=(
                    "No author is recorded in the metadata. Many tools omit "
                    "this field by default."
                ),
            )
        return None

    # ── 9 ──────────────────────────────────────────────────────────

    def _check_xmp_date_mismatch(self, metadata: ExtractedMetadata) -> Finding | None:
        xmp = metadata.xmp_metadata
        if xmp is None:
            return None

        xmp_create = xmp.get("xmp_create_date")
        xmp_modify = xmp.get("xmp_modify_date")
        if not xmp_create and not xmp_modify:
            return None

        threshold = timedelta(seconds=60)
        details: list[str] = []

        for doc_val, xmp_key, label in [
            (metadata.created_date, "xmp_create_date", "creation"),
            (metadata.modified_date, "xmp_modify_date", "modification"),
        ]:
            xmp_val = xmp.get(xmp_key)
            if not doc_val or not xmp_val:
                continue
            try:
                doc_dt = dateparser.parse(doc_val)
                xmp_dt = dateparser.parse(xmp_val)
                delta = abs((doc_dt - xmp_dt).total_seconds())
                if delta > threshold.total_seconds():
                    details.append(
                        f"DocInfo {label.capitalize()}Date: {doc_val}\n"
                        f"XMP xmp:CreateDate: {xmp_val}\n"
                        f"Delta: {int(delta)} seconds"
                    )
            except Exception:
                continue

        if not details:
            return None

        return Finding(
            title="XMP and document info date mismatch",
            severity="Medium",
            confidence=0.7,
            explanation=(
                "The XMP metadata dates differ from the document "
                "information dictionary dates. In unmodified documents "
                "these values are usually consistent. A mismatch may "
                "suggest selective metadata editing."
            ),
            technical_detail="\n---\n".join(details),
        )

    # ── 10 ─────────────────────────────────────────────────────────

    def _check_is_encrypted(self, metadata: ExtractedMetadata) -> Finding | None:
        if metadata.is_encrypted is True:
            return Finding(
                title="Document is encrypted",
                severity="Low",
                confidence=0.4,
                explanation=(
                    "The document has encryption applied. While encryption is "
                    "normal for protected documents, it can also limit metadata "
                    "verification."
                ),
            )
        return None


    # ── 11 ─────────────────────────────────────────────────────────

    def _check_multiple_saved_revisions(self, metadata: ExtractedMetadata) -> Finding | None:
        inc = metadata.incremental_updates
        if inc is None or not inc.get("has_incremental_updates"):
            return None
        count = inc.get("revision_count", 1)
        positions = inc.get("revision_positions", [])
        severity: str = "Medium" if count == 2 else "High"
        return Finding(
            title="PDF contains multiple saved revisions",
            severity=severity,
            confidence=0.75,
            explanation=(
                f"This PDF contains {count} revision layers, meaning "
                "it was saved multiple times after its original creation. Each save "
                "may represent an edit. While re-saving is normal, multiple revisions "
                "in a sensitive document may warrant closer review."
            ),
            technical_detail=f"%%EOF markers found at byte offsets: {positions}",
        )

    # ── 12 ─────────────────────────────────────────────────────────

    def _check_high_revision_count(self, metadata: ExtractedMetadata) -> Finding | None:
        inc = metadata.incremental_updates
        if inc is None:
            return None
        count = inc.get("revision_count", 0)
        if count <= 3:
            return None
        return Finding(
            title="High revision count detected",
            severity="High",
            confidence=0.8,
            explanation=(
                f"The document contains {count} incremental updates, "
                "which is unusually high for a standard document. This strongly "
                "suggests the file was edited multiple times after its original creation."
            ),
        )


    # ── 13 ─────────────────────────────────────────────────────────

    def _check_xmp_creator_tool_mismatch(self, metadata: ExtractedMetadata) -> Finding | None:
        xmp = metadata.xmp_metadata
        if xmp is None:
            return None
        xmp_tool = xmp.get("xmp_creator_tool")
        producer = metadata.producer
        if not xmp_tool or not producer:
            return None
        xt = xmp_tool.lower().strip()
        pt = producer.lower().strip()
        if xt == pt or xt in pt or pt in xt:
            return None
        return Finding(
            title="XMP creator tool differs from document producer",
            severity="Low",
            confidence=0.5,
            explanation=(
                "The tool recorded in XMP metadata differs from "
                "the producer field in the document information dictionary. "
                "This inconsistency can occur when metadata is partially updated."
            ),
        )


checker = MetadataChecker()
