import type { ExtractedMetadata } from "../types";
import { formatDate } from "../utils";

interface Props {
  metadata: ExtractedMetadata;
}

const fields: { label: string; key: keyof ExtractedMetadata; format?: (v: string) => string }[] = [
  { label: "File Name", key: "file_name" },
  { label: "File Size (bytes)", key: "file_size_bytes" },
  { label: "File Type", key: "file_type" },
  { label: "PDF Version", key: "pdf_version" },
  { label: "Created Date", key: "created_date", format: formatDate },
  { label: "Modified Date", key: "modified_date", format: formatDate },
  { label: "Author", key: "author" },
  { label: "Creator", key: "creator" },
  { label: "Producer", key: "producer" },
  { label: "Title", key: "title" },
  { label: "Subject", key: "subject" },
  { label: "Page Count", key: "page_count" },
  { label: "Encrypted", key: "is_encrypted" },
];

const highlightDates = new Set(["created_date", "modified_date"]);

export default function MetadataTable({ metadata }: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-700">
      <table className="w-full text-sm">
        <tbody>
          {fields.map(({ label, key, format }) => {
            const raw = metadata[key];
            const missing = raw === null || raw === undefined || raw === "";
            const display = missing ? "\u2014" : format ? format(String(raw)) : String(raw);
            const highlight = highlightDates.has(key) && missing;

            return (
              <tr key={key} className={highlight ? "bg-amber-900/20" : "even:bg-zinc-800/30"}>
                <td className="px-4 py-2.5 text-zinc-400 font-medium whitespace-nowrap w-1/3">
                  {label}
                </td>
                <td className={`px-4 py-2.5 ${missing ? "text-zinc-600 italic" : "text-zinc-200"}`}>
                  {display}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
