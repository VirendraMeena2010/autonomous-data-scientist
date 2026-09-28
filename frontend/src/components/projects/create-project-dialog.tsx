import { AlertCircle, LoaderCircle, Plus } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useCreateProject } from "@/hooks/use-projects";

interface ProjectFormValues {
  name: string;
  description: string;
}

interface CreateProjectDialogProps {
  children?: ReactNode;
}

export function CreateProjectDialog({
  children,
}: CreateProjectDialogProps) {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<ProjectFormValues>({
    name: "",
    description: "",
  });
  const [nameError, setNameError] = useState<string | null>(null);

  function resetDialog() {
    setValues({ name: "", description: "" });
    setNameError(null);
    createProject.reset();
  }

  function handleOpenChange(nextOpen: boolean) {
    if (createProject.isPending) {
      return;
    }

    setOpen(nextOpen);

    if (!nextOpen) {
      resetDialog();
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const name = values.name.trim();

    if (!name) {
      setNameError("Enter a project name.");
      return;
    }

    if (name.length > 120) {
      setNameError("Use 120 characters or fewer.");
      return;
    }

    setNameError(null);

    createProject.mutate(
      {
        name,
        description: values.description.trim(),
      },
      {
        onSuccess: (project) => {
          setOpen(false);
          resetDialog();
          toast.success("Project created.");
          void navigate(`/projects/${project.id}`);
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {children ?? (
          <Button>
            <Plus aria-hidden="true" />
            New Project
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create project</DialogTitle>
          <DialogDescription>
            Create a workspace for related datasets and analyses.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
          className="space-y-5"
          noValidate
        >
          <div className="space-y-2">
            <label htmlFor="project-name" className="text-sm font-medium">
              Project name
            </label>

            <Input
              id="project-name"
              value={values.name}
              onChange={(event) => {
                setValues((current) => ({
                  ...current,
                  name: event.target.value,
                }));
                setNameError(null);
              }}
              placeholder="e.g. Sales performance"
              maxLength={120}
              disabled={createProject.isPending}
              aria-invalid={Boolean(nameError) || undefined}
              aria-describedby={nameError ? "project-name-error" : undefined}
              autoFocus
            />

            {nameError && (
              <p
                id="project-name-error"
                className="flex items-center gap-1.5 text-xs text-destructive"
              >
                <AlertCircle className="size-3.5" aria-hidden="true" />
                {nameError}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-4">
              <label
                htmlFor="project-description"
                className="text-sm font-medium"
              >
                Description
              </label>

              <span className="text-xs text-muted-foreground">
                {values.description.length}/500
              </span>
            </div>

            <Textarea
              id="project-description"
              value={values.description}
              onChange={(event) => {
                setValues((current) => ({
                  ...current,
                  description: event.target.value,
                }));
              }}
              placeholder="What will you investigate in this project?"
              maxLength={500}
              disabled={createProject.isPending}
            />
          </div>

          {createProject.error && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive"
            >
              <AlertCircle
                className="mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              <p>{createProject.error.message}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={createProject.isPending}
              onClick={() => {
                handleOpenChange(false);
              }}
            >
              Cancel
            </Button>

            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending && (
                <LoaderCircle className="animate-spin" aria-hidden="true" />
              )}
              {createProject.isPending ? "Creating…" : "Create Project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
