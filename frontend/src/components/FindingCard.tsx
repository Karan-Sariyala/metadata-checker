import { useState } from "react";
import type { Finding } from "../types";

interface Props {
  finding: Finding;
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

export default function FindingCard({ finding }: Props) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(finding.confidence * 100);

  return (
    <div className={`border-l-4 ${borderColors[finding.severity]} bg-zinc-800/50 rounded-r-xl p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-semibold">{finding.title}</h4>
          <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded ${badgeColors[finding.severity]}`}>
            {finding.severity}
          </span>
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-center gap-2 text-xs text-zinc-400 mb-1">
          <span>Confidence</span>
          <span className="font-mono text-zinc-300">{pct}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-zinc-700 overflow-hidden">
          <div
            className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <p className="mt-3 text-sm text-zinc-300 leading-relaxed">{finding.explanation}</p>

      {finding.technical_detail && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-zinc-500 hover:text-zinc-300 underline"
          >
            {expanded ? "Hide technical detail" : "Show technical detail"}
          </button>
          {expanded && (
            <pre className="mt-2 text-xs text-zinc-400 bg-zinc-900 rounded p-2 overflow-x-auto whitespace-pre-wrap">
              {finding.technical_detail}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
