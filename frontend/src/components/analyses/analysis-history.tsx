import {
  AlertCircle,
  ArrowUpRight,
  FileSpreadsheet,
  History,
  RefreshCw,
  ScanSearch,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAnalyses } from "@/hooks/use-analyses";
import { useDatasets } from "@/hooks/use-datasets";
import type {
  Analysis,
  AnalysisStatus,
} from "@/types/analysis";

interface AnalysisHistoryProps {
  projectId: string;
}

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

function formatRelativeTime(value: string | undefined): string {
  if (!value) {
    return "Recently";
  }

  const timestamp = new Date(value).getTime();

  if (!Number.isFinite(timestamp)) {
    return "Recently";
  }

  const elapsedSeconds = Math.max(
    0,
    Math.floor((Date.now() - timestamp) / 1000),
  );

  if (elapsedSeconds < 60) {
    return "Just now";
  }

  const elapsedMinutes = Math.floor(elapsedSeconds / 60);

  if (elapsedMinutes < 60) {
    return `${elapsedMinutes}m ago`;
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60);

  if (elapsedHours < 24) {
    return `${elapsedHours}h ago`;
  }

  const elapsedDays = Math.floor(elapsedHours / 24);

  if (elapsedDays < 7) {
    return `${elapsedDays}d ago`;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year:
      new Date(value).getFullYear() !== new Date().getFullYear()
        ? "numeric"
        : undefined,
  }).format(new Date(value));
}

function HistorySkeleton() {
  return (
    <div className="space-y-2" aria-label="Loading analyses">
      {Array.from({ length: 3 }, (_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-lg border bg-card p-4"
        >
          <div className="flex items-center justify-between gap-4">
            <div className="h-4 w-3/5 rounded bg-muted" />
            <div className="h-5 w-20 rounded-full bg-muted" />
          </div>
          <div className="mt-3 h-3 w-2/5 rounded bg-muted/70" />
        </div>
      ))}
    </div>
  );
}

function HistoryRow({
  projectId,
  analysis,
  datasetName,
}: {
  projectId: string;
  analysis: Analysis;
  datasetName: string;
}) {
  const statusMeta = getStatusMeta(analysis.status);

  return (
    <li>
      <Link
        to={`/projects/${projectId}/analyses/${analysis.id}`}
        className="group flex items-center gap-3 rounded-lg border bg-card p-4 shadow-sm outline-none transition-colors hover:border-muted-foreground/30 hover:bg-card/80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background sm:gap-4"
      >
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md border bg-muted/40">
          <ScanSearch
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />
        </span>

        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium">
            {analysis.question}
          </span>

          <span className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <FileSpreadsheet className="size-3" aria-hidden="true" />
            <span className="truncate">{datasetName}</span>
          </span>
        </span>

        <span className="hidden shrink-0 text-xs text-muted-foreground sm:block">
          {formatRelativeTime(analysis.created_at)}
        </span>

        <Badge variant={statusMeta.variant}>
          {statusMeta.label}
        </Badge>

        <ArrowUpRight
          className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
          aria-hidden="true"
        />
      </Link>
    </li>
  );
}

export function AnalysisHistory({ projectId }: AnalysisHistoryProps) {
  const analysesQuery = useAnalyses(projectId);
  const datasetsQuery = useDatasets(projectId);

  const analyses = analysesQuery.data ?? [];
  const datasets = datasetsQuery.data ?? [];
  const isLoading = analysesQuery.isPending || datasetsQuery.isPending;
  const hasError = analysesQuery.isError || datasetsQuery.isError;
  const error =
    analysesQuery.error ?? datasetsQuery.error ?? null;

  return (
    <section aria-labelledby="analysis-history-heading" className="space-y-4">
      <div>
        <h2
          id="analysis-history-heading"
          className="text-lg font-semibold tracking-tight"
        >
          Recent analyses
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Questions investigated in this project.
        </p>
      </div>

      {isLoading && <HistorySkeleton />}

      {hasError && (
        <div className="rounded-lg border bg-card p-8 text-center shadow-sm">
          <span className="mx-auto flex size-10 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle
              className="size-5 text-destructive"
              aria-hidden="true"
            />
          </span>

          <h3 className="mt-4 text-base font-medium">
            Analyses could not be loaded
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            {error?.message ??
              "The analysis history could not be loaded."}
          </p>

          <Button
            className="mt-5"
            variant="outline"
            onClick={() => {
              if (analysesQuery.isError) {
                void analysesQuery.refetch();
              }

              if (datasetsQuery.isError) {
                void datasetsQuery.refetch();
              }
            }}
          >
            <RefreshCw aria-hidden="true" />
            Try again
          </Button>
        </div>
      )}

      {!isLoading && !hasError && analyses.length === 0 && (
        <div className="rounded-lg border border-dashed bg-card px-6 py-14 text-center shadow-sm">
          <span className="mx-auto flex size-12 items-center justify-center rounded-xl border bg-muted/50">
            <History
              className="size-5 text-muted-foreground"
              aria-hidden="true"
            />
          </span>

          <h3 className="mt-5 text-lg font-semibold tracking-tight">
            No analyses yet
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            Open a dataset and ask your first question about the data.
          </p>
        </div>
      )}

      {!isLoading && !hasError && analyses.length > 0 && (
        <ul className="space-y-2" aria-label="Recent analyses">
          {analyses.slice(0, 10).map((analysis) => {
            const dataset = datasets.find(
              (item) => item.id === analysis.dataset_id,
            );

            return (
              <HistoryRow
                key={analysis.id}
                projectId={projectId}
                analysis={analysis}
                datasetName={dataset?.original_filename ?? "Unknown dataset"}
              />
            );
          })}
        </ul>
      )}
    </section>
  );
}
