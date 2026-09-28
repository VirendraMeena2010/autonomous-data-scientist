import {
  AlertTriangle,
  LoaderCircle,
  MoreHorizontal,
} from "lucide-react";
import { useState, type ReactNode } from "react";
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
import { useDeleteProject } from "@/hooks/use-projects";

interface ProjectDeleteDialogProps {
  projectId: string;
  projectName: string;
  children?: ReactNode;
}

export function ProjectDeleteDialog({
  projectId,
  projectName,
  children,
}: ProjectDeleteDialogProps) {
  const navigate = useNavigate();
  const deleteProject = useDeleteProject();
  const [open, setOpen] = useState(false);

  function handleOpenChange(nextOpen: boolean) {
    if (!deleteProject.isPending) {
      setOpen(nextOpen);
    }
  }

  function handleDelete() {
    deleteProject.mutate(projectId, {
      onSuccess: () => {
        setOpen(false);
        toast.success("Project deleted.");
        void navigate("/projects", { replace: true });
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {children ?? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Project actions"
            title="Project actions"
          >
            <MoreHorizontal aria-hidden="true" />
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle
              className="size-5 text-destructive"
              aria-hidden="true"
            />
            Delete project?
          </DialogTitle>

          <DialogDescription>
            This will permanently delete{" "}
            <span className="font-medium text-foreground">
              {projectName}
            </span>{" "}
            and its associated datasets and analyses. This action cannot be
            undone.
          </DialogDescription>
        </DialogHeader>

        {deleteProject.error && (
          <div
            role="alert"
            className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm leading-5 text-destructive"
          >
            {deleteProject.error.message}
          </div>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={deleteProject.isPending}
            onClick={() => {
              handleOpenChange(false);
            }}
          >
            Cancel
          </Button>

          <Button
            type="button"
            variant="destructive"
            disabled={deleteProject.isPending}
            onClick={handleDelete}
          >
            {deleteProject.isPending ? (
              <LoaderCircle className="animate-spin" aria-hidden="true" />
            ) : (
              <AlertTriangle aria-hidden="true" />
            )}
            {deleteProject.isPending ? "Deleting…" : "Delete Project"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
