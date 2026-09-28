import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import * as analysesApi from "@/api/analyses";
import type {
  Analysis,
  AnalysisExportFormat,
  AnalysisStatus,
} from "@/types/analysis";

function isPendingStatus(status: AnalysisStatus | undefined): boolean {
  return status === "queued" || status === "running";
}

export function useAnalyses(projectId: string) {
  return useQuery({
    queryKey: ["analyses", projectId],
    queryFn: () => analysesApi.listAnalyses(projectId),
    enabled: Boolean(projectId),
  });
}

export function useAnalysis(
  projectId: string,
  analysisId: string,
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: ["analyses", projectId, analysisId],
    queryFn: () => analysesApi.getAnalysis(projectId, analysisId),
    enabled: Boolean(
      projectId &&
        analysisId &&
        (options?.enabled === undefined || options.enabled),
    ),
    refetchInterval: (query) => {
      const analysis: Analysis | undefined = query.state.data;

      if (!analysis || !isPendingStatus(analysis.status)) {
        return false;
      }

      return 3000;
    },
  });
}

export function useCreateAnalysis(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: { dataset_id: string; question: string }) =>
      analysesApi.createAnalysis(projectId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analyses", projectId] });
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "summary"],
      });
    },
  });
}

export function useRetryAnalysis(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (analysisId: string) =>
      analysesApi.retryAnalysis(projectId, analysisId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analyses", projectId] });
    },
  });
}

export function useCancelAnalysis(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (analysisId: string) =>
      analysesApi.cancelAnalysis(projectId, analysisId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analyses", projectId] });
    },
  });
}

export function useExportAnalysis(projectId: string) {
  return useMutation({
    mutationFn: ({
      analysisId,
      format,
    }: {
      analysisId: string;
      format: AnalysisExportFormat;
    }) => analysesApi.exportAnalysis(projectId, analysisId, format),
  });
}
