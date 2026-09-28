import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { NewAnalysisDialog } from "@/components/analyses/new-analysis-dialog";
import { DatasetUploadDialog } from "@/components/datasets/dataset-upload-dialog";
import { ProjectDeleteDialog } from "@/components/projects/project-delete-dialog";
import { Badge } from "@/components/ui/badge";
import type { Project } from "@/types/project";

interface ProjectWorkspaceHeaderProps {
  project: Project;
}

export function ProjectWorkspaceHeader({
  project,
}: ProjectWorkspaceHeaderProps) {
  return (
    <header className="border-b pb-7">
      <Link
        to="/projects"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" aria-hidden="true" />
        Projects
      </Link>

      <div className="mt-5 flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div className="min-w-0">
          <Badge variant="secondary">Project workspace</Badge>

          <h1 className="mt-3 wrap-break-word text-3xl font-semibold tracking-[-0.035em]">
            {project.name}
          </h1>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            {project.description?.trim() ||
              "Organize datasets, questions, and analytical investigations."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <DatasetUploadDialog projectId={project.id} />
          <NewAnalysisDialog projectId={project.id} />
          <ProjectDeleteDialog
            projectId={project.id}
            projectName={project.name}
          />
        </div>
      </div>
    </header>
  );
}
