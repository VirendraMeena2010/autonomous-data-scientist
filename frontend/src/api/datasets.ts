import { ApiError, apiRequest, isRecord } from "@/api/client";
import type { Dataset } from "@/types/dataset";

export async function listDatasets(projectId: string): Promise<Dataset[]> {
  return apiRequest<Dataset[]>(
    `projects/${encodeURIComponent(projectId)}/datasets`,
  );
}

export async function getDataset(
  projectId: string,
  datasetId: string,
): Promise<Dataset> {
  return apiRequest<Dataset>(
    `projects/${encodeURIComponent(projectId)}/datasets/${encodeURIComponent(datasetId)}`,
  );
}

export async function uploadDataset(
  projectId: string,
  file: File,
): Promise<Dataset> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<Dataset>(
    `projects/${encodeURIComponent(projectId)}/datasets`,
    {
      method: "POST",
      body: formData,
    },
  );
}

export async function deleteDataset(
  projectId: string,
  datasetId: string,
): Promise<void> {
  await apiRequest<void>(
    `projects/${encodeURIComponent(projectId)}/datasets/${encodeURIComponent(datasetId)}`,
    {
      method: "DELETE",
    },
  );
}

export async function getDatasetDownloadUrl(
  projectId: string,
  datasetId: string,
): Promise<string> {
  const payload = await apiRequest<unknown>(
    `projects/${encodeURIComponent(projectId)}/datasets/${encodeURIComponent(datasetId)}/download-url`,
  );

  const url = readDownloadUrl(payload);

  if (!url) {
    throw new ApiError(
      502,
      "The download link could not be created. Please try again.",
    );
  }

  return url;
}

function readDownloadUrl(payload: unknown): string | null {
  if (typeof payload === "string") {
    return payload.trim() || null;
  }

  if (!isRecord(payload)) {
    return null;
  }

  const nestedData = isRecord(payload.data) ? payload.data : null;

  const candidate =
    payload.download_url ??
    payload.downloadUrl ??
    payload.url ??
    payload.signed_url ??
    payload.href ??
    nestedData?.download_url ??
    nestedData?.downloadUrl ??
    nestedData?.url ??
    nestedData?.signed_url ??
    nestedData?.href;

  return typeof candidate === "string" && candidate.trim()
    ? candidate.trim()
    : null;
}
