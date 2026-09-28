import {
  ArrowRight,
  Database,
  FolderKanban,
  ScanSearch,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { Project } from "@/types/project";

interface ProjectCardProps {
  project: Project;
}

function formatUpdatedAt(value: string | undefined): string {
  if (!value) {
    return "Recently updated";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Recently updated";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
  }).format(date);
}

export function ProjectCard({ project }: ProjectCardProps) {
  const description = project.description?.trim();
  const hasDatasetCount =
    typeof project.dataset_count === "number";
  const hasAnalysisCount =
    typeof project.analysis_count === "number";

  return (
    <Link
      to={`/projects/${project.id}`}
      prefetch="intent"
      className="group flex min-h-56 flex-col rounded-lg border bg-card p-5 shadow-sm outline-none transition-colors hover:border-muted-foreground/30 hover:bg-card/80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <div className="flex items-start justify-between gap-4">
        <span className="flex size-9 items-center justify-center rounded-md border bg-muted/60">
          <FolderKanban
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />
        </span>

        <ArrowRight
          className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5"
          aria-hidden="true"
        />
      </div>

      <div className="mt-6 flex-1">
        <h2 className="truncate text-base font-semibold tracking-tight">
          {project.name}
        </h2>

        <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
          {description || "No project description provided."}
        </p>
      </div>

      <div className="mt-6 flex items-center gap-4 border-t pt-4 text-xs text-muted-foreground">
        {hasDatasetCount && (
          <span className="inline-flex items-center gap-1.5">
            <Database className="size-3.5" aria-hidden="true" />
            {project.dataset_count} datasets
          </span>
        )}

        {hasAnalysisCount && (
          <span className="inline-flex items-center gap-1.5">
            <ScanSearch className="size-3.5" aria-hidden="true" />
            {project.analysis_count} analyses
          </span>
        )}

        <span className="ml-auto whitespace-nowrap">
          {formatUpdatedAt(project.updated_at)}
        </span>
      </div>
    </Link>
  );
}
