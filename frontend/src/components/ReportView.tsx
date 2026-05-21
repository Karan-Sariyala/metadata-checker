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

const PDF_API = "http://localhost:8080/api/analyze/pdf-report";

const simpleSummary: Record<string, string> = {
  Low: "A few minor metadata signals were found. Nothing out of the ordinary.",
  Medium:
    "Some metadata patterns caught our attention. They don't confirm anything unusual, but are worth a quick look.",
  High:
    "This document has multiple metadata signals that suggest it may have been edited or processed after its original creation. You may want to verify it independently.",
};

export default function ReportView({ report, onReset, uploadedFile }: Props) {
  const [mode, setMode] = useState<"simple" | "technical">("simple");
  const [jsonOpen, setJsonOpen] = useState(false);

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
    } catch {
      // silently fail — PDF download error
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0 flex-1">
          <h2 className="text-xl font-bold text-white">
            {report.document_name}
          </h2>
          <p className="text-sm text-zinc-500">{report.file_type}</p>
        </div>
        <div className="flex items-center gap-4 flex-wrap">
          <RiskBadge
            level={report.metadata_risk_level}
            score={report.metadata_risk_score}
          />
          <RiskDonut
            findings={report.findings}
            totalScore={report.metadata_risk_score}
            riskLevel={report.metadata_risk_level}
          />
        </div>
      </div>

      <div className="bg-zinc-800/40 rounded-xl p-4 border border-zinc-700">
        <p className="text-zinc-300 text-sm leading-relaxed">
          {mode === "simple"
            ? simpleSummary[report.metadata_risk_level] ?? report.summary
            : report.summary}
        </p>
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
            Findings ({report.findings.length})
          </h3>
          <ModeToggle mode={mode} onToggle={setMode} />
        </div>
        <div className="space-y-3">
          {report.findings.map((f, i) => (
            <FindingCard key={i} finding={f} mode={mode} />
          ))}
        </div>
      </section>

      <ForensicTimeline
        metadata={report.extracted_metadata}
        findings={report.findings}
      />

      <section>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Extracted Metadata
        </h3>
        <MetadataTable metadata={report.extracted_metadata} />
      </section>

      <div className="bg-zinc-800/60 rounded-xl border border-zinc-700 p-4">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
          Recommended Action
        </p>
        <p className="text-zinc-200 text-sm">{report.recommended_action}</p>
      </div>

      {mode === "technical" && (
        <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 overflow-hidden">
          <button
            onClick={() => setJsonOpen(!jsonOpen)}
            className="w-full flex items-center justify-between px-4 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider hover:text-zinc-200 transition-colors"
          >
            <span>Raw Metadata JSON</span>
            <span className="text-zinc-500">{jsonOpen ? "▲" : "▼"}</span>
          </button>
          {jsonOpen && (
            <pre className="p-4 text-xs text-zinc-400 bg-zinc-900 overflow-x-auto whitespace-pre-wrap font-mono border-t border-zinc-700 max-h-96 overflow-y-auto">
              {JSON.stringify(report, null, 2)}
            </pre>
          )}
        </div>
      )}

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
          onClick={onReset}
          className="px-5 py-2.5 rounded-lg border border-zinc-600 hover:border-zinc-500 text-zinc-300 text-sm font-medium transition-colors"
        >
          Analyze Another
        </button>
      </div>
    </div>
  );
}
