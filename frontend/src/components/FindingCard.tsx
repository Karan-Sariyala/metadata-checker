import type { Finding } from "../types";

interface Props {
  finding: Finding;
  mode: "simple" | "technical";
}

const borderColors: Record<string, string> = {
  Low: "border-l-blue-500",
  Medium: "border-l-amber-500",
  High: "border-l-red-500",
};

const badgeColors: Record<string, string> = {
  Low: "bg-blue-900/50 text-blue-300",
  Medium: "bg-amber-900/50 text-amber-300",
  High: "bg-red-900/50 text-red-300",
};

const simpleTitles: Record<string, string> = {
  "Modified date precedes creation date": "Timeline doesn't add up",
  "Creator and producer mismatch": "Made with one tool, saved with another",
  "Known editing tool in metadata": "Editing software detected",
  "PDF contains multiple saved revisions": "File was saved multiple times",
  "High revision count detected": "File was edited many times",
  "XMP and document info date mismatch": "Internal dates don't match each other",
  "Missing creation date": "No creation date recorded",
  "Both dates missing": "No date information found",
  "Document is encrypted": "Document is password-protected",
  "Author field is empty": "No author recorded",
};

function confidenceLabel(c: number): string {
  if (c <= 0.4) return "Low";
  if (c <= 0.7) return "Medium";
  return "High";
}

export default function FindingCard({ finding, mode }: Props) {
  const pct = Math.round(finding.confidence * 100);
  const title =
    mode === "simple"
      ? simpleTitles[finding.title] ?? finding.title
      : finding.title;

  return (
    <div
      className={`border-l-4 ${borderColors[finding.severity]} bg-zinc-800/50 rounded-r-xl p-4`}
    >
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-white font-semibold">{title}</h4>
      </div>

      {mode === "simple" ? (
        <>
          <p className="mt-2 text-xs text-zinc-400">
            Confidence: {confidenceLabel(finding.confidence)}
          </p>
          <p className="mt-1 text-sm text-zinc-300 leading-relaxed">
            {finding.explanation}
          </p>
        </>
      ) : (
        <>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded ${badgeColors[finding.severity]}`}
            >
              {finding.severity}
            </span>
            <span className="text-xs text-zinc-500 font-mono">{pct}%</span>
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-zinc-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-500 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-3 text-sm text-zinc-300 leading-relaxed">
            {finding.explanation}
          </p>
          {finding.technical_detail && (
            <pre className="mt-3 text-xs text-zinc-400 bg-zinc-900 rounded p-2 overflow-x-auto whitespace-pre-wrap font-mono">
              {finding.technical_detail}
            </pre>
          )}
        </>
      )}
    </div>
  );
}
