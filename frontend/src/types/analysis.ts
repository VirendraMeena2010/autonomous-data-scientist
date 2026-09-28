import type { JsonObject } from "@/types/dataset";

export type AnalysisStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "guardrail_blocked";

export interface Finding {
  finding?: string;
  title?: string;
  evidence?: unknown;
  confidence?: string | number;
  impact?: string;
  explanation?: string;
  [key: string]: unknown;
}

export type AnalysisPlan = string | JsonObject | null;
export type AnalysisProfile = string | JsonObject | null;
export type AnalysisQuality = string | JsonObject | null;
export type AnalysisReport = string | JsonObject | null;
export type AnalysisGuardrail = string | JsonObject | null;

export interface Analysis {
  id: string;
  project_id: string;
  owner_id?: string;
  dataset_id: string;
  question: string;
  status: AnalysisStatus;
  attempt?: number;
  plan: AnalysisPlan;
  profile: AnalysisProfile;
  quality: AnalysisQuality;
  findings: Finding[];
  report: AnalysisReport;
  guardrail: AnalysisGuardrail;
  langfuse_trace_id?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface CreateAnalysisInput {
  dataset_id: string;
  question: string;
}

export interface CreatedAnalysis {
  id: string;
}

export type AnalysisExportFormat = "json" | "markdown";
