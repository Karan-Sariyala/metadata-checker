import { useState } from "react";
import axios from "axios";
import type { AnalysisReport } from "./types";
import UploadZone from "./components/UploadZone";
import ReportView from "./components/ReportView";

const API_URL = "http://localhost:8080/api/analyze";

export default function App() {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await axios.post<AnalysisReport>(API_URL, fd);
      setReport(data);
    } catch (e: unknown) {
      if (axios.isAxiosError(e) && e.response?.data?.detail) {
        setError(e.response.data.detail);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setReport(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex flex-col items-center px-4 py-12">
      <div style={{ maxWidth: 860 }} className="w-full">
        <header className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white">Document Metadata Checker</h1>
          <p className="text-zinc-500 mt-1 text-sm">
            Upload a document to inspect its metadata and assess privacy risks
          </p>
        </header>

        {report ? (
          <ReportView report={report} onReset={reset} />
        ) : (
          <UploadZone onAnalyze={handleAnalyze} loading={loading} error={error} />
        )}
      </div>
    </div>
  );
}
