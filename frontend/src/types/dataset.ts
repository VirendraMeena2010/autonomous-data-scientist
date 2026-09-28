export type JsonObject = Record<string, unknown>;

export interface Dataset {
  id: string;
  project_id: string;
  owner_id?: string;
  original_filename: string;
  stored_path?: string;
  media_type?: string | null;
  size_bytes: number | null;
  sha256?: string | null;
  row_count: number | null;
  column_count: number | null;
  status: string;
  metadata: JsonObject | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}
