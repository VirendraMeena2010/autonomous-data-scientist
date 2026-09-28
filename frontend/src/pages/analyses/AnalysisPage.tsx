import {
  AlertCircle,
  ArrowLeft,
  Ban,
  CheckCircle2,
  Clock3,
  FileSpreadsheet,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  TriangleAlert,
} from "lucide-react";
import { Link, Navigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { AnalysisActions } from "@/components/analyses/analysis-actions";
import { AnalysisResults } from "@/components/analyses/analysis-results";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  useAnalysis,
  useCancelAnalysis,
  useRetryAnalysis,
} from "@/hooks/use-analyses";
import { useDatasets } from "@/hooks/use-datasets";
import type { AnalysisStatus } from "@/types/analysis";

function getStatusMeta(status: AnalysisStatus): {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
} {
  switch (status) {
    case "queued":
      return { label: "Queued", variant: "outline" };
    case "running":
      return { label: "Running", variant: "default" };
    case "succeeded":
      return { label: "Completed", variant: "secondary" };
    case "failed":
      return { label: "Failed", variant: "destructive" };
    case "cancelled":
      return { label: "Cancelled", variant: "outline" };
    case "guardrail_blocked":
      return { label: "Guardrail blocked", variant: "destructive" };
  }
}

function getGuardrailMessage(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    return null;
  }

  const record = value as Record<string, unknown>;
  const keys = ["reason", "message", "detail", "explanation", "description"];

  for (const key of keys) {
    const candidate = record[key];

    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }

  return null;
}

function AnalysisPageSkeleton() {
  return (
    <div className="animate-pulse space-y-8" aria-label="Loading analysis">
      <div className="space-y-4 border-b pb-7">
        <div className="h-4 w-28 rounded bg-muted" />
        <div className="h-8 w-136 max-w-full rounded bg-muted" />
        <div className="h-4 w-52 rounded bg-muted/70" />
      </div>

      <div className="h-28 rounded-lg border bg-card" />
      <div className="h-72 rounded-lg border bg-card" />
      <div className="h-96 rounded-lg border bg-card" />
    </div>
  );
}

interface LifecycleCardProps {
  status: AnalysisStatus;
  errorMessage?: string | null;
  guardrailMessage?: string | null;
  isMutating: boolean;
  onCancel: () => void;
  onRetry: () => void;
}

function LifecycleCard({
  status,
  errorMessage,
  guardrailMessage,
  isMutating,
  onCancel,
  onRetry,
}: LifecycleCardProps) {
  if (status === "queued" || status === "running") {
    const running = status === "running";

    return (
      <Card className="gap-0 py-0 shadow-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="flex flex-col items-center px-4 py-10 text-center sm:py-14">
            <div
              className="flex size-12 items-center justify-center rounded-full bg-secondary"
              aria-hidden="true"
            >
              {running ? (
                <LoaderCircle className="size-5 animate-spin" />
              ) : (
                <Clock3 className="size-5" />
              )}
            </div>

            <h2 className="mt-5 text-xl font-semibold tracking-tight">
              {running ? "Analyzing your dataset" : "Analysis queued"}
            </h2>

            <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
              {running
                ? "The autonomous data scientist is investigating your question."
                : "Your dataset is waiting to be analyzed."}
            </p>

            <div
              className="mt-7 flex items-center gap-1.5"
              role="status"
              aria-live="polite"
            >
              <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/40" />
              <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/60 [animation-delay:150ms]" />
              <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
            </div>

            <Button
              type="button"
              variant="outline"
              className="mt-8"
              disabled={isMutating}
              onClick={onCancel}
            >
              {isMutating ? (
                <LoaderCircle className="animate-spin" aria-hidden="true" />
              ) : (
                <Ban aria-hidden="true" />
              )}
              Cancel analysis
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status === "guardrail_blocked") {
    return (
      <Card className="border-amber-500/30 bg-amber-500/5 gap-0 py-0 shadow-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="flex items-start gap-4">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <TriangleAlert className="size-5" aria-hidden="true" />
            </span>

            <div className="min-w-0">
              <h2 className="text-lg font-semibold tracking-tight">
                Analysis couldn&apos;t be completed
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                The requested analysis was blocked by the system&apos;s
                analysis constraints.
              </p>

              {guardrailMessage && (
                <div className="mt-5 rounded-md border bg-background/70 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Reason
                  </p>
                  <p className="mt-2 text-sm leading-6">
                    {guardrailMessage}
                  </p>
                </div>
              )}

              <Button
                type="button"
                variant="outline"
                className="mt-6"
                disabled={isMutating}
                onClick={onRetry}
              >
                {isMutating ? (
                  <LoaderCircle className="animate-spin" aria-hidden="true" />
                ) : (
                  <RotateCcw aria-hidden="true" />
                )}
                Try another question
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status === "failed") {
    return (
      <Card className="border-destructive/25 gap-0 py-0 shadow-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="flex items-start gap-4">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertCircle className="size-5" aria-hidden="true" />
            </span>

            <div className="min-w-0">
              <h2 className="text-lg font-semibold tracking-tight">
                Analysis failed
              </h2>

              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                We couldn&apos;t complete this analysis.
              </p>

              {errorMessage && (
                <p className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm leading-6 text-destructive">
                  {errorMessage}
                </p>
              )}

              <Button
                type="button"
                className="mt-6"
                disabled={isMutating}
                onClick={onRetry}
              >
                {isMutating ? (
                  <LoaderCircle className="animate-spin" aria-hidden="true" />
                ) : (
                  <RotateCcw aria-hidden="true" />
                )}
                Retry analysis
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status === "cancelled") {
    return (
      <Card className="gap-0 py-0 shadow-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="flex items-start gap-4">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted">
              <Ban
                className="size-5 text-muted-foreground"
                aria-hidden="true"
              />
            </span>

            <div>
              <h2 className="text-lg font-semibold tracking-tight">
                Analysis cancelled
              </h2>

              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                This analysis was cancelled before completion.
              </p>

              <Button
                type="button"
                variant="outline"
                className="mt-6"
                disabled={isMutating}
                onClick={onRetry}
              >
                {isMutating ? (
                  <LoaderCircle className="animate-spin" aria-hidden="true" />
                ) : (
                  <RotateCcw aria-hidden="true" />
                )}
                Run again
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardContent className="p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-secondary">
            <CheckCircle2
              className="size-5 text-foreground"
              aria-hidden="true"
            />
          </span>

          <div>
            <h2 className="text-lg font-semibold tracking-tight">
              Analysis completed
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              The analysis service returned a completed result.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AnalysisPage() {
  const { projectId, analysisId } = useParams<{
    projectId: string;
    datasetId: string;
    analysisId: string;
  }>();

  const analysisQuery = useAnalysis(projectId ?? "", analysisId ?? "");
  const datasetsQuery = useDatasets(projectId ?? "");
  const cancelAnalysis = useCancelAnalysis(projectId ?? "");
  const retryAnalysis = useRetryAnalysis(projectId ?? "");

  if (!projectId || !analysisId) {
    return <Navigate to="/projects" replace />;
  }

  if (analysisQuery.isPending) {
    return <AnalysisPageSkeleton />;
  }

  if (analysisQuery.isError) {
    return (
      <div className="rounded-lg border bg-card px-6 py-14 text-center shadow-sm">
        <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle
            className="size-5 text-destructive"
            aria-hidden="true"
          />
        </span>

        <h1 className="mt-5 text-lg font-semibold">
          Analysis could not be loaded
        </h1>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          {analysisQuery.error.message}
        </p>

        <div className="mt-6 flex justify-center gap-3">
          <Button variant="outline" asChild>
            <Link to={`/projects/${projectId}`}>Back to project</Link>
          </Button>

          <Button
            disabled={analysisQuery.isFetching}
            onClick={() => {
              void analysisQuery.refetch();
            }}
          >
            <RefreshCw
              className={
                analysisQuery.isFetching ? "animate-spin" : undefined
              }
              aria-hidden="true"
            />
            Try again
          </Button>
        </div>
      </div>
    );
  }

  const analysis = analysisQuery.data;
  const statusMeta = getStatusMeta(analysis.status);
  const dataset = datasetsQuery.data?.find(
    (item) => item.id === analysis.dataset_id,
  );
  const guardrailMessage = getGuardrailMessage(analysis.guardrail);
  const isMutating =
    cancelAnalysis.isPending || retryAnalysis.isPending;

  function handleCancel() {
    cancelAnalysis.mutate(analysis.id, {
      onSuccess: () => {
        toast.success("Analysis cancellation requested.");
        void analysisQuery.refetch();
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  }

  function handleRetry() {
    retryAnalysis.mutate(analysis.id, {
      onSuccess: () => {
        toast.success("A new analysis attempt was requested.");
        void analysisQuery.refetch();
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  }

  return (
    <div className="space-y-8">
      <header className="border-b pb-7">
        <Link
          to={`/projects/${projectId}`}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" aria-hidden="true" />
          Back to project
        </Link>

        <div className="mt-6 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                Analysis
              </p>
              <Badge variant={statusMeta.variant}>
                {statusMeta.label}
              </Badge>
            </div>

            <h1 className="mt-3 max-w-4xl wrap-break-word text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">
              {analysis.question}
            </h1>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              <FileSpreadsheet className="size-4" aria-hidden="true" />

              {dataset ? (
                <Link
                  to={`/projects/${projectId}/datasets/${dataset.id}`}
                  className="hover:text-foreground hover:underline"
                >
                  {dataset.original_filename}
                </Link>
              ) : (
                <span>Dataset</span>
              )}

              {typeof analysis.attempt === "number" && (
                <>
                  <span aria-hidden="true">·</span>
                  <span>Attempt {analysis.attempt}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <AnalysisActions
        projectId={projectId}
        analysis={analysis}
      />

      {analysis.status === "succeeded" ? (
        <AnalysisResults analysis={analysis} />
      ) : (
        <LifecycleCard
          status={analysis.status}
          errorMessage={analysis.error_message}
          guardrailMessage={guardrailMessage}
          isMutating={isMutating}
          onCancel={handleCancel}
          onRetry={handleRetry}
        />
      )}
    </div>
  );
}
