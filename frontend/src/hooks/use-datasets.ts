import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import * as datasetsApi from "@/api/datasets";

export function useDatasets(projectId: string) {
  return useQuery({
    queryKey: ["datasets", projectId],
    queryFn: () => datasetsApi.listDatasets(projectId),
    enabled: Boolean(projectId),
  });
}

export function useDataset(projectId: string, datasetId: string) {
  return useQuery({
    queryKey: ["datasets", projectId, datasetId],
    queryFn: () => datasetsApi.getDataset(projectId, datasetId),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useUploadDataset(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => datasetsApi.uploadDataset(projectId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets", projectId] });
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId],
      });
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "summary"],
      });
    },
  });
}

export function useDeleteDataset(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (datasetId: string) =>
      datasetsApi.deleteDataset(projectId, datasetId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets", projectId] });
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId],
      });
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "summary"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["analyses", projectId],
      });
    },
  });
}

export function useDownloadDataset(projectId: string) {
  return useMutation({
    mutationFn: (datasetId: string) =>
      datasetsApi.getDatasetDownloadUrl(projectId, datasetId),
  });
}
