import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import * as projectsApi from "@/api/projects";
import type {
  CreateProjectInput,
} from "@/types/project";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.listProjects,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => projectsApi.getProject(projectId),
    enabled: Boolean(projectId),
  });
}

export function useProjectSummary(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId, "summary"],
    queryFn: () => projectsApi.getProjectSummary(projectId),
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateProjectInput) => projectsApi.createProject(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsApi.deleteProject(projectId),
    onSuccess: (deletedProjectId: string) => {
      queryClient.removeQueries({
        queryKey: ["projects", deletedProjectId],
      });
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
