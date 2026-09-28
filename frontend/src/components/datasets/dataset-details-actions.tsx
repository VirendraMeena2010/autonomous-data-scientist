import {
  LoaderCircle,
  MoreHorizontal,
  Trash2,
  TriangleAlert,
} from "lucide-react";
import { useRef, useState } from "react";
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
} from "@/components/ui/dialog";
import { useDeleteDataset } from "@/hooks/use-datasets";
import type { Dataset } from "@/types/dataset";

interface DatasetDetailsActionsProps {
  projectId: string;
  dataset: Dataset;
}

export function DatasetDetailsActions({
  projectId,
  dataset,
}: DatasetDetailsActionsProps) {
  const navigate = useNavigate();
  const deleteDataset = useDeleteDataset(projectId);
  const menuRef = useRef<HTMLDetailsElement>(null);

  const [deleteOpen, setDeleteOpen] = useState(false);

  function openDeleteDialog() {
    menuRef.current?.removeAttribute("open");
    setDeleteOpen(true);
  }

  function handleDelete() {
    deleteDataset.mutate(dataset.id, {
      onSuccess: () => {
        setDeleteOpen(false);
        toast.success("Dataset deleted.");
        void navigate(`/projects/${projectId}`, { replace: true });
      },
    });
  }

  return (
    <>
      <details ref={menuRef} className="group relative">
        <summary
          className="flex size-9 list-none items-center justify-center rounded-md border bg-background text-sm font-medium shadow-xs transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 [&::-webkit-details-marker]:hidden"
          aria-label="Dataset actions"
        >
          <MoreHorizontal className="size-4" aria-hidden="true" />
          <span className="sr-only">More</span>
        </summary>

        <div className="absolute right-0 top-[calc(100%+8px)] z-40 w-48 rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-lg">
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm text-destructive outline-none transition-colors hover:bg-destructive/10 focus-visible:bg-destructive/10 focus-visible:ring-2 focus-visible:ring-ring"
            onClick={openDeleteDialog}
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Delete dataset
          </button>
        </div>
      </details>

      <Dialog
        open={deleteOpen}
        onOpenChange={(open) => {
          if (!deleteDataset.isPending) {
            setDeleteOpen(open);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TriangleAlert
                className="size-5 text-destructive"
                aria-hidden="true"
              />
              Delete dataset?
            </DialogTitle>

            <DialogDescription>
              This will permanently delete{" "}
              <span className="font-medium text-foreground">
                {dataset.original_filename}
              </span>{" "}
              and any analyses associated with it. This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>

          {deleteDataset.isError && (
            <div
              role="alert"
              className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm leading-5 text-destructive"
            >
              {deleteDataset.error.message}
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={deleteDataset.isPending}
              onClick={() => {
                setDeleteOpen(false);
              }}
            >
              Cancel
            </Button>

            <Button
              type="button"
              variant="destructive"
              disabled={deleteDataset.isPending}
              onClick={handleDelete}
            >
              {deleteDataset.isPending ? (
                <LoaderCircle
                  className="animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Trash2 aria-hidden="true" />
              )}
              {deleteDataset.isPending ? "Deleting…" : "Delete Dataset"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
