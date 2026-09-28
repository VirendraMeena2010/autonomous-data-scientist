import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  LoaderCircle,
  UploadCloud,
  X,
} from "lucide-react";
import {
  useRef,
  useState,
  type DragEvent,
  type FormEvent,
  type ReactNode,
} from "react";
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
import { useUploadDataset } from "@/hooks/use-datasets";
import { cn } from "@/lib/utils";

interface DatasetUploadDialogProps {
  projectId: string;
  children?: ReactNode;
}

function isCsvFile(file: File): boolean {
  return file.name.toLowerCase().endsWith(".csv");
}

export function DatasetUploadDialog({
  projectId,
  children,
}: DatasetUploadDialogProps) {
  const uploadDataset = useUploadDataset(projectId);
  const inputRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function resetDialog() {
    setFile(null);
    setFileError(null);
    setIsDragging(false);
    uploadDataset.reset();

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    if (uploadDataset.isPending) {
      return;
    }

    setOpen(nextOpen);

    if (!nextOpen) {
      resetDialog();
    }
  }

  function selectFile(nextFile: File | null) {
    setFileError(null);

    if (!nextFile) {
      return;
    }

    if (!isCsvFile(nextFile)) {
      setFile(null);
      setFileError("Please choose a CSV file.");
      return;
    }

    if (nextFile.size === 0) {
      setFile(null);
      setFileError("The selected file is empty.");
      return;
    }

    setFile(nextFile);
  }

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files.item(0));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setFileError("Choose a CSV file before uploading.");
      return;
    }

    uploadDataset.mutate(file, {
      onSuccess: () => {
        setOpen(false);
        resetDialog();
        toast.success("Dataset uploaded successfully.");
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {children ?? (
          <Button>
            <UploadCloud aria-hidden="true" />
            Upload Dataset
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload dataset</DialogTitle>
          <DialogDescription>
            Upload a CSV file to begin an autonomous investigation.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
          className="space-y-5"
          noValidate
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(event) => {
              selectFile(event.target.files?.item(0) ?? null);
            }}
          />

          <button
            type="button"
            className={cn(
              "group flex min-h-48 w-full flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center outline-none transition-colors",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              isDragging
                ? "border-primary bg-secondary"
                : "border-muted-foreground/35 bg-muted/30 hover:border-muted-foreground/60 hover:bg-muted/50",
            )}
            onClick={() => {
              inputRef.current?.click();
            }}
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(event) => {
              if (event.currentTarget === event.target) {
                setIsDragging(false);
              }
            }}
            onDrop={handleDrop}
          >
            <span className="flex size-11 items-center justify-center rounded-xl border bg-card shadow-sm">
              <FileSpreadsheet
                className="size-5 text-muted-foreground"
                aria-hidden="true"
              />
            </span>

            <span className="mt-4 text-sm font-medium">
              Drop a CSV file here
            </span>

            <span className="mt-1 text-xs text-muted-foreground">
              or click to browse your files
            </span>
          </button>

          {file && (
            <div className="flex items-center gap-3 rounded-md border bg-muted/30 p-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-background">
                <FileSpreadsheet
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </span>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {file.name}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>

              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Remove ${file.name}`}
                disabled={uploadDataset.isPending}
                onClick={() => {
                  setFile(null);
                  setFileError(null);

                  if (inputRef.current) {
                    inputRef.current.value = "";
                  }
                }}
              >
                <X aria-hidden="true" />
              </Button>
            </div>
          )}

          {uploadDataset.isPending && (
            <div className="space-y-2" role="status" aria-live="polite">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <LoaderCircle
                  className="size-3.5 animate-spin"
                  aria-hidden="true"
                />
                Uploading dataset…
              </div>

              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-pulse rounded-full bg-primary" />
              </div>
            </div>
          )}

          {fileError && (
            <p
              role="alert"
              className="flex items-center gap-1.5 text-xs text-destructive"
            >
              <AlertCircle className="size-3.5" aria-hidden="true" />
              {fileError}
            </p>
          )}

          {uploadDataset.isError && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm leading-5 text-destructive"
            >
              <AlertCircle
                className="mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              <p>{uploadDataset.error.message}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={uploadDataset.isPending}
              onClick={() => {
                handleOpenChange(false);
              }}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={!file || uploadDataset.isPending}
            >
              {uploadDataset.isPending ? (
                <LoaderCircle
                  className="animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <UploadCloud aria-hidden="true" />
              )}
              {uploadDataset.isPending ? "Uploading…" : "Upload Dataset"}
            </Button>
          </DialogFooter>
        </form>

        <p className="flex items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
          <CheckCircle2 className="size-3.5" aria-hidden="true" />
          Your file will be available for analysis after upload.
        </p>
      </DialogContent>
    </Dialog>
  );
}
