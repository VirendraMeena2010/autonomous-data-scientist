import {
  Download,
  FileJson,
  FileText,
  LoaderCircle,
  RotateCcw,
  X,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCancelAnalysis, useExportAnalysis, useRetryAnalysis } from "@/hooks/use-analyses";
import type { Analysis } from "@/types/analysis";

interface AnalysisActionsProps {
  projectId: string;
  analysis: Analysis;
}

export function AnalysisActions({
  projectId,
  analysis,
}: AnalysisActionsProps) {
  const exportAnalysis = useExportAnalysis(projectId);
  const retryAnalysis = useRetryAnalysis(projectId);
  const cancelAnalysis = useCancelAnalysis(projectId);
  const [menuOpen, setMenuOpen] = useState(false);

  const isPending = analysis.status === "queued" || analysis.status === "running";
  const isMutating =
    exportAnalysis.isPending ||
    retryAnalysis.isPending ||
    cancelAnalysis.isPending;

  function downloadFile(blob: Blob, filename: string) {
    const objectUrl = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    window.URL.revokeObjectURL(objectUrl);
  }

  function handleExport(format: "json" | "markdown") {
    setMenuOpen(false);

    exportAnalysis.mutate(
      {
        analysisId: analysis.id,
        format,
      },
      {
        onSuccess: (file) => {
          downloadFile(file.blob, file.filename);
          toast.success(`Analysis exported as ${format.toUpperCase()}.`);
        },
        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  }

  function handleRetry() {
    setMenuOpen(false);

    retryAnalysis.mutate(analysis.id, {
      onSuccess: () => {
        toast.success("A new analysis attempt was requested.");
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  }

  function handleCancel() {
    setMenuOpen(false);

    cancelAnalysis.mutate(analysis.id, {
      onSuccess: () => {
        toast.success("Analysis cancellation requested.");
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  }

  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium">Analysis actions</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Export the completed result or manage this analysis run.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Button
              type="button"
              variant="outline"
              disabled={isPending || isMutating}
              onClick={() => {
                setMenuOpen((current) => !current);
              }}
              aria-expanded={menuOpen}
              aria-haspopup="menu"
            >
              {exportAnalysis.isPending ? (
                <LoaderCircle className="animate-spin" aria-hidden="true" />
              ) : (
                <Download aria-hidden="true" />
              )}
              Export
            </Button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute right-0 top-[calc(100%+8px)] z-40 w-44 rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-lg"
              >
                <button
                  type="button"
                  role="menuitem"
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
                  onClick={() => {
                    handleExport("markdown");
                  }}
                >
                  <FileText className="size-4" aria-hidden="true" />
                  Markdown
                </button>

                <button
                  type="button"
                  role="menuitem"
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
                  onClick={() => {
                    handleExport("json");
                  }}
                >
                  <FileJson className="size-4" aria-hidden="true" />
                  JSON
                </button>
              </div>
            )}
          </div>

          {analysis.status !== "succeeded" && (
            <Button
              type="button"
              variant="outline"
              disabled={isPending || isMutating}
              onClick={handleRetry}
            >
              {retryAnalysis.isPending ? (
                <LoaderCircle className="animate-spin" aria-hidden="true" />
              ) : (
                <RotateCcw aria-hidden="true" />
              )}
              Retry
            </Button>
          )}

          {isPending && (
            <Button
              type="button"
              variant="outline"
              disabled={isMutating}
              onClick={handleCancel}
            >
              {cancelAnalysis.isPending ? (
                <LoaderCircle className="animate-spin" aria-hidden="true" />
              ) : (
                <X aria-hidden="true" />
              )}
              Cancel
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
