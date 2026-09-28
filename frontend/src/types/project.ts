export interface Project {
  id: string;
  name: string;
  description?: string | null;
  owner_id?: string;
  dataset_count?: number | null;
  analysis_count?: number | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface ProjectSummary {
  project_id: string;
  dataset_count: number | null;
  analysis_count: number | null;
  succeeded_count: number | null;
  failed_count: number | null;
  success_rate: number | null;
}

export interface CreateProjectInput {
  name: string;
  description: string;
}
