import { AlertCircle, FolderKanban, Plus, RefreshCw } from "lucide-react";

import { CreateProjectDialog } from "@/components/projects/create-project-dialog";
import { ProjectCard } from "@/components/projects/project-card";
import { Button } from "@/components/ui/button";
import { useProjects } from "@/hooks/use-projects";

function ProjectsSkeleton() {
  return (
    <div
      className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
      aria-label="Loading projects"
    >
      {Array.from({ length: 6 }, (_, index) => (
        <div
          key={index}
          className="min-h-56 animate-pulse rounded-lg border bg-card p-5 shadow-sm"
        >
          <div className="size-9 rounded-md bg-muted" />
          <div className="mt-7 h-5 w-1/2 rounded bg-muted" />
          <div className="mt-3 h-4 w-full rounded bg-muted/80" />
          <div className="mt-2 h-4 w-3/4 rounded bg-muted/80" />
          <div className="mt-10 h-px bg-border" />
        </div>
      ))}
    </div>
  );
}

export default function Projects() {
  const projectsQuery = useProjects();

  return (
    <div className="space-y-8">
      <header className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm text-muted-foreground">
            Your analysis workspaces
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em]">
            Projects
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            Organize datasets, questions, and autonomous analyses.
          </p>
        </div>

        <CreateProjectDialog />
      </header>

      {projectsQuery.isPending && <ProjectsSkeleton />}

      {projectsQuery.isError && (
        <div className="rounded-lg border bg-card p-8 text-center shadow-sm">
          <span className="mx-auto flex size-10 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle
              className="size-5 text-destructive"
              aria-hidden="true"
            />
          </span>

          <h2 className="mt-4 text-base font-medium">
            Projects could not be loaded
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            {projectsQuery.error.message}
          </p>

          <Button
            className="mt-5"
            variant="outline"
            disabled={projectsQuery.isFetching}
            onClick={() => {
              void projectsQuery.refetch();
            }}
          >
            <RefreshCw
              className={
                projectsQuery.isFetching ? "animate-spin" : undefined
              }
              aria-hidden="true"
            />
            {projectsQuery.isFetching ? "Retrying…" : "Try again"}
          </Button>
        </div>
      )}

      {projectsQuery.isSuccess && projectsQuery.data.length === 0 && (
        <section className="rounded-lg border border-dashed bg-card px-6 py-16 text-center shadow-sm">
          <span className="mx-auto flex size-12 items-center justify-center rounded-xl border bg-muted/50">
            <FolderKanban
              className="size-5 text-muted-foreground"
              aria-hidden="true"
            />
          </span>

          <h2 className="mt-5 text-lg font-semibold tracking-tight">
            Start your first analysis workspace
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            Create a project to organize datasets, questions, and AI-generated
            analyses.
          </p>

          <div className="mt-6">
            <CreateProjectDialog>
              <Button>
                <Plus aria-hidden="true" />
                Create Project
              </Button>
            </CreateProjectDialog>
          </div>
        </section>
      )}

      {projectsQuery.isSuccess && projectsQuery.data.length > 0 && (
        <section
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
          aria-label="Projects"
        >
          {projectsQuery.data.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </section>
      )}
    </div>
  );
}
