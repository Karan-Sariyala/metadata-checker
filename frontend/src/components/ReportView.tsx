import type { AnalysisReport } from "../types";
import RiskBadge from "./RiskBadge";
import MetadataTable from "./MetadataTable";
import FindingCard from "./FindingCard";

interface Props {
  report: AnalysisReport;
  onReset: () => void;
}

export default function ReportView({ report, onReset }: Props) {
  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.document_name.replace(/\.[^.]+$/, "")}_metadata_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-white">{report.document_name}</h2>
          <p className="text-sm text-zinc-500">{report.file_type}</p>
        </div>
        <RiskBadge level={report.metadata_risk_level} score={report.metadata_risk_score} />
      </div>

      <div className="bg-zinc-800/40 rounded-xl p-4 border border-zinc-700">
        <p className="text-zinc-300 text-sm leading-relaxed">{report.summary}</p>
      </div>

      <section>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Extracted Metadata
        </h3>
        <MetadataTable metadata={report.extracted_metadata} />
      </section>

      <section>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Findings ({report.findings.length})
        </h3>
        <div className="space-y-3">
          {report.findings.map((f, i) => (
            <FindingCard key={i} finding={f} />
          ))}
        </div>
      </section>

      <div className="bg-zinc-800/60 rounded-xl border border-zinc-700 p-4">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
          Recommended Action
        </p>
        <p className="text-zinc-200 text-sm">{report.recommended_action}</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <button
          onClick={handleDownload}
          className="px-5 py-2.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-white text-sm font-medium transition-colors"
        >
          Download JSON Report
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
