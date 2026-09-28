import { apiRequest } from "@/api/client";
import type {
  CreateProjectInput,
  Project,
  ProjectSummary,
} from "@/types/project";

export async function listProjects(): Promise<Project[]> {
  return apiRequest<Project[]>("projects");
}

export async function getProject(projectId: string): Promise<Project> {
  return apiRequest<Project>(`projects/${encodeURIComponent(projectId)}`);
}

export async function getProjectSummary(
  projectId: string,
): Promise<ProjectSummary> {
  return apiRequest<ProjectSummary>(
    `projects/${encodeURIComponent(projectId)}/summary`,
  );
}

export async function createProject(
  input: CreateProjectInput,
): Promise<Project> {
  return apiRequest<Project>("projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiRequest<void>(`projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
  });
}
