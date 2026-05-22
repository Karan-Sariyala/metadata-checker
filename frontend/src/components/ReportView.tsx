import { useState } from "react";
import axios from "axios";
import type { AnalysisReport } from "../types";
import RiskBadge from "./RiskBadge";
import MetadataTable from "./MetadataTable";
import FindingCard from "./FindingCard";
import ModeToggle from "./ModeToggle";
import ForensicTimeline from "./ForensicTimeline";
import RiskDonut from "./RiskDonut";

interface Props {
  report: AnalysisReport;
  onReset: () => void;
  uploadedFile: File | null;
}

const PDF_API = "http://localhost:8000/api/analyze/pdf-report";

const simpleSummary: Record<string, string> = {
  Low: "A few minor metadata signals were found. Nothing out of the ordinary.",
  Medium:
    "Some metadata patterns caught our attention. They don't confirm anything unusual, but are worth a quick look.",
  High:
    "This document has multiple metadata signals that suggest it may have been edited or processed after its original creation. You may want to verify it independently.",
};

export default function ReportView({ report, onReset, uploadedFile }: Props) {
  const [mode, setMode] = useState<"basic" | "detailed">("basic");
  const [jsonOpen, setJsonOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.document_name.replace(/\.[^.]+$/, "")}_metadata_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    if (!uploadedFile) return;
    try {
      const fd = new FormData();
      fd.append("file", uploadedFile);
      const { data } = await axios.post(PDF_API, fd, { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${uploadedFile.name.replace(/\.[^.]+$/, "")}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {}
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0 flex-1">
          <h2 className="text-xl font-bold text-white">
            {report.document_name}
          </h2>
          <p className="text-sm text-zinc-500">{report.file_type}</p>
        </div>
        <ModeToggle mode={mode} onToggle={setMode} />
      </div>

      {/* Summary */}
      <div className="bg-zinc-800/40 rounded-xl p-5 border border-zinc-700">
        <p className="text-zinc-300 text-sm leading-relaxed">
          {mode === "basic"
            ? simpleSummary[report.metadata_risk_level] ?? report.summary
            : report.summary}
        </p>
      </div>

      {/* Risk Overview */}
      <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 p-5">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">
          Risk Overview
        </h3>
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <RiskBadge
            level={report.metadata_risk_level}
            score={report.metadata_risk_score}
          />
          <div className="w-px h-16 bg-zinc-700 hidden sm:block" />
          <RiskDonut
            findings={report.findings}
            riskLevel={report.metadata_risk_level}
          />
        </div>
      </div>

      {/* Signals */}
      <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 p-5">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">
          Signals ({report.findings.length})
        </h3>
        <div className="space-y-3">
          {report.findings.map((f, i) => (
            <FindingCard key={i} finding={f} mode={mode} />
          ))}
        </div>
      </div>

      {/* Document History */}
      <ForensicTimeline
        metadata={report.extracted_metadata}
        findings={report.findings}
      />

      {/* Properties */}
      <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 overflow-hidden">
        <div className="p-5 pb-0">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
            Document Properties
          </h3>
        </div>
        <MetadataTable metadata={report.extracted_metadata} />
      </div>

      {/* Next Steps */}
      <div className="bg-zinc-800/60 rounded-xl border border-zinc-700 p-5">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
          Next Steps
        </p>
        <p className="text-zinc-200 text-sm leading-relaxed">{report.recommended_action}</p>
      </div>

      {/* Raw JSON (detailed mode only) */}
      {mode === "detailed" && (
        <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 overflow-hidden">
          <button
            onClick={() => setJsonOpen(!jsonOpen)}
            className="w-full flex items-center justify-between px-5 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider hover:text-zinc-200 transition-colors"
          >
            <span>Full Report Data</span>
            <span className="text-zinc-500">{jsonOpen ? "▲" : "▼"}</span>
          </button>
          {jsonOpen && (
            <pre className="p-5 text-xs text-zinc-400 bg-zinc-900 overflow-x-auto whitespace-pre-wrap font-mono border-t border-zinc-700 max-h-96 overflow-y-auto">
              {JSON.stringify(report, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={handleDownloadJson}
          className="px-5 py-2.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-white text-sm font-medium transition-colors"
        >
          Download JSON
        </button>
        <button
          onClick={handleDownloadPdf}
          disabled={!uploadedFile}
          className="px-5 py-2.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-white text-sm font-medium transition-colors disabled:opacity-40"
        >
          Download PDF Report
        </button>
        <button
          onClick={handleCopyJson}
          className="px-5 py-2.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-white text-sm font-medium transition-colors"
        >
          {copied ? "Copied!" : "Copy JSON"}
        </button>
        <button
          onClick={onReset}
          className="px-5 py-2.5 rounded-lg border border-zinc-600 hover:border-zinc-500 text-zinc-300 text-sm font-medium transition-colors"
        >
          Analyze Another
        </button>
      </div>
    </div>
  );
}
