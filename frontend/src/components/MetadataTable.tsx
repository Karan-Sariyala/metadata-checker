import type { ExtractedMetadata } from "../types";

interface Props {
  metadata: ExtractedMetadata;
}

const fields: { label: string; key: keyof ExtractedMetadata }[] = [
  { label: "File Name", key: "file_name" },
  { label: "File Size (bytes)", key: "file_size_bytes" },
  { label: "File Type", key: "file_type" },
  { label: "PDF Version", key: "pdf_version" },
  { label: "Created Date", key: "created_date" },
  { label: "Modified Date", key: "modified_date" },
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
          {fields.map(({ label, key }) => {
            const value = metadata[key];
            const missing = value === null || value === undefined || value === "";
            const highlight = highlightDates.has(key) && missing;

            return (
              <tr key={key} className={highlight ? "bg-amber-900/20" : "even:bg-zinc-800/30"}>
                <td className="px-4 py-2.5 text-zinc-400 font-medium whitespace-nowrap w-1/3">
                  {label}
                </td>
                <td className={`px-4 py-2.5 ${missing ? "text-zinc-600 italic" : "text-zinc-200"}`}>
                  {missing ? "\u2014" : String(value)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
