export interface ExtractedMetadata {
  file_name: string;
  file_size_bytes: number;
  file_type: string;
  pdf_version: string | null;
  created_date: string | null;
  modified_date: string | null;
  author: string | null;
  creator: string | null;
  producer: string | null;
  title: string | null;
  subject: string | null;
  page_count: number | null;
  is_encrypted: boolean | null;
  xmp_metadata: Record<string, unknown> | null;
  raw_info: Record<string, unknown> | null;
  incremental_updates: Record<string, unknown> | null;
}

export interface Finding {
  title: string;
  severity: "Low" | "Medium" | "High";
  confidence: number;
  explanation: string;
  technical_detail: string | null;
}

export interface AnalysisReport {
  document_name: string;
  file_type: string;
  metadata_risk_score: number;
  metadata_risk_level: "Low" | "Medium" | "High";
  summary: string;
  extracted_metadata: ExtractedMetadata;
  findings: Finding[];
  recommended_action: string;
}
