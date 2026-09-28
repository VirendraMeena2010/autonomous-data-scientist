import {
  ApiError,
  apiDownload,
  apiRequest,
  isRecord,
} from "@/api/client";
import type {
  Analysis,
  AnalysisExportFormat,
  CreateAnalysisInput,
  CreatedAnalysis,
} from "@/types/analysis";

function readCreatedAnalysisId(payload: unknown): string | null {
  if (!isRecord(payload)) {
    return null;
  }

  const nestedData = isRecord(payload.data) ? payload.data : null;

  const candidate =
    payload.analysis_id ??
    payload.analysisId ??
    payload.id ??
    nestedData?.analysis_id ??
    nestedData?.analysisId ??
    nestedData?.id;

  return typeof candidate === "string" && candidate.trim()
    ? candidate.trim()
    : null;
}

export async function listAnalyses(
  projectId: string,
): Promise<Analysis[]> {
  return apiRequest<Analysis[]>(
    `projects/${encodeURIComponent(projectId)}/analyses`,
  );
}

export async function getAnalysis(
  projectId: string,
  analysisId: string,
): Promise<Analysis> {
  return apiRequest<Analysis>(
    `projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}`,
  );
}

export async function createAnalysis(
  projectId: string,
  input: CreateAnalysisInput,
): Promise<CreatedAnalysis> {
  const payload = await apiRequest<unknown>(
    `projects/${encodeURIComponent(projectId)}/analyses`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );

  const id = readCreatedAnalysisId(payload);

  if (!id) {
    throw new ApiError(
      502,
      "The analysis was created, but its identifier could not be read. Please try again.",
    );
  }

  return { id };
}

export async function retryAnalysis(
  projectId: string,
  analysisId: string,
): Promise<Analysis> {
  return apiRequest<Analysis>(
    `projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}/retry`,
    {
      method: "POST",
    },
  );
}

export async function cancelAnalysis(
  projectId: string,
  analysisId: string,
): Promise<Analysis> {
  return apiRequest<Analysis>(
    `projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}/cancel`,
    {
      method: "POST",
    },
  );
}

export async function exportAnalysis(
  projectId: string,
  analysisId: string,
  format: AnalysisExportFormat,
): Promise<{ blob: Blob; filename: string }> {
  return apiDownload(
    `projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}/export?format=${encodeURIComponent(format)}`,
  );
}
