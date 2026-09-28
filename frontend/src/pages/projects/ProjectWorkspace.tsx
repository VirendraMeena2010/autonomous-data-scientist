import {
  AlertCircle,
  Database,
  FileCheck2,
  MessageSquareText,
  RefreshCw,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";
import { Link, Navigate, useParams } from "react-router-dom";

import { AnalysisHistory } from "@/components/analyses/analysis-history";
import { DatasetList } from "@/components/datasets/dataset-list";
import { ProjectSummary } from "@/components/projects/project-summary";
import { ProjectWorkspaceHeader } from "@/components/projects/project-workspace-header";
import { Button } from "@/components/ui/button";
import {
  useProject,
  useProjectSummary,
} from "@/hooks/use-projects";

interface WorkflowStep {
  label: string;
  description: string;
  icon: LucideIcon;
}

const WORKFLOW_STEPS: readonly WorkflowStep[] = [
  {
    label: "Upload",
    description: "Add a source dataset",
    icon: Database,
  },
  {
    label: "Ask",
    description: "Frame a question",
    icon: MessageSquareText,
  },
  {
    label: "Analyze",
    description: "Run autonomous investigation",
    icon: ScanSearch,
  },
  {
    label: "Understand",
    description: "Review evidence and findings",
    icon: FileCheck2,
  },
];

function WorkspaceWorkflow() {
  return (
    <section
      aria-labelledby="workspace-workflow-heading"
      className="rounded-lg border bg-card px-4 py-4 shadow-sm sm:px-5"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <div className="shrink-0 lg:w-40">
          <h2
            id="workspace-workflow-heading"
            className="text-sm font-semibold tracking-tight"
          >
            Investigation flow
          </h2>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            From source data to insight.
          </p>
        </div>

        <ol className="grid flex-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {WORKFLOW_STEPS.map(
            ({ label, description, icon: Icon }, index) => (
              <li
                key={label}
                className="relative flex items-center gap-3 rounded-md border bg-muted/20 px-3 py-3"
              >
                <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-background text-muted-foreground shadow-xs">
                  <Icon className="size-3.5" aria-hidden="true" />
                </span>

                <span className="min-w-0">
                  <span className="block text-xs font-medium">
                    {label}
                  </span>
                  <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                    {description}
                  </span>
                </span>

                {index < WORKFLOW_STEPS.length - 1 && (
                  <span
                    aria-hidden="true"
                    className="absolute -right-2 top-1/2 hidden -translate-y-1/2 text-muted-foreground/50 xl:block"
                  >
                    →
                  </span>
                )}
              </li>
            ),
          )}
        </ol>
      </div>
    </section>
  );
}

function ProjectWorkspaceSkeleton() {
  return (
    <div className="animate-pulse space-y-8" aria-label="Loading project">
      <div className="space-y-4 border-b pb-7">
        <div className="h-4 w-24 rounded bg-muted" />
        <div className="h-9 w-72 max-w-full rounded bg-muted" />
        <div className="h-4 w-136 max-w-full rounded bg-muted" />
        <div className="flex gap-2 pt-2">
          <div className="h-9 w-32 rounded-md bg-muted" />
          <div className="h-9 w-32 rounded-md bg-muted" />
          <div className="h-9 w-9 rounded-md bg-muted" />
        </div>
      </div>

      <div>
        <div className="h-4 w-20 rounded bg-muted" />
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="h-32 rounded-lg border bg-card p-4"
            >
              <div className="h-3 w-20 rounded bg-muted" />
              <div className="mt-5 h-7 w-16 rounded bg-muted" />
              <div className="mt-3 h-3 w-28 rounded bg-muted/70" />
            </div>
          ))}
        </div>
      </div>

      <div className="h-24 rounded-lg border bg-card" />

      <div className="space-y-3">
        <div className="h-5 w-24 rounded bg-muted" />

        {Array.from({ length: 2 }, (_, index) => (
          <div
            key={index}
            className="h-24 rounded-lg border bg-card"
          />
        ))}
      </div>
    </div>
  );
}

export default function ProjectWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();

  const projectQuery = useProject(projectId ?? "");
  const summaryQuery = useProjectSummary(projectId ?? "");

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (projectQuery.isPending) {
    return <ProjectWorkspaceSkeleton />;
  }

  if (projectQuery.isError) {
    return (
      <div className="rounded-lg border bg-card px-6 py-14 text-center shadow-sm">
        <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle
            className="size-5 text-destructive"
            aria-hidden="true"
          />
        </span>

        <h1 className="mt-5 text-lg font-semibold">
          Project could not be loaded
        </h1>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          {projectQuery.error.message}
        </p>

        <div className="mt-6 flex justify-center gap-3">
          <Button variant="outline" asChild>
            <Link to="/projects">Back to projects</Link>
          </Button>

          <Button
            disabled={projectQuery.isFetching}
            onClick={() => {
              void projectQuery.refetch();
            }}
          >
            <RefreshCw
              className={
                projectQuery.isFetching ? "animate-spin" : undefined
              }
              aria-hidden="true"
            />
            Try again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <ProjectWorkspaceHeader project={projectQuery.data} />

      <ProjectSummary
        summary={summaryQuery.data}
        isLoading={summaryQuery.isPending}
        error={summaryQuery.error}
      />

      <WorkspaceWorkflow />

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] xl:items-start">
        <DatasetList projectId={projectId} />
        <AnalysisHistory projectId={projectId} />
      </div>
    </div>
  );
}
