import {
  AlertCircle,
  ArrowLeft,
  Download,
  FileSpreadsheet,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import { Link, Navigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { AnalysisComposer } from "@/components/analyses/analysis-composer";
import { DatasetDetailsActions } from "@/components/datasets/dataset-details-actions";
import { DatasetMetadata } from "@/components/datasets/dataset-metadata";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  useDataset,
  useDownloadDataset,
} from "@/hooks/use-datasets";

function formatCount(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat().format(value)
    : "—";
}

function formatSize(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "—";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string | undefined): string {
  if (!value) {
    return "Recently";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year:
      date.getFullYear() !== new Date().getFullYear()
        ? "numeric"
        : undefined,
  }).format(date);
}

function getFileType(dataset: {
  media_type?: string | null;
  original_filename: string;
}): string {
  if (dataset.media_type) {
    return dataset.media_type.split("/").pop()?.toUpperCase() ?? "DATASET";
  }

  return (
    dataset.original_filename.split(".").pop()?.toUpperCase() ??
    "DATASET"
  );
}

function getStatusVariant(
  status: string,
): "secondary" | "destructive" | "outline" {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "failed") {
    return "destructive";
  }

  if (
    normalizedStatus === "ready" ||
    normalizedStatus === "completed" ||
    normalizedStatus === "succeeded"
  ) {
    return "secondary";
  }

  return "outline";
}

function DatasetDetailsSkeleton() {
  return (
    <div className="animate-pulse space-y-8" aria-label="Loading dataset">
      <div className="space-y-4 border-b pb-7">
        <div className="h-4 w-36 rounded bg-muted" />
        <div className="flex items-center gap-3">
          <div className="size-12 rounded-lg bg-muted" />
          <div className="space-y-2">
            <div className="h-8 w-72 max-w-full rounded bg-muted" />
            <div className="h-4 w-56 rounded bg-muted/70" />
          </div>
        </div>
      </div>

      <div>
        <div className="h-5 w-36 rounded bg-muted" />
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="h-28 rounded-lg border bg-card p-4"
            >
              <div className="h-3 w-20 rounded bg-muted" />
              <div className="mt-5 h-7 w-16 rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>

      <div className="h-64 rounded-lg border bg-card" />
    </div>
  );
}

interface OverviewMetricProps {
  label: string;
  value: string;
  detail: string;
}

function OverviewMetric({
  label,
  value,
  detail,
}: OverviewMetricProps) {
  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground">
          {label}
        </p>
        <p className="mt-3 text-2xl font-semibold tracking-[-0.03em]">
          {value}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

export default function DatasetDetails() {
  const { projectId, datasetId } = useParams<{
    projectId: string;
    datasetId: string;
  }>();

  const datasetQuery = useDataset(projectId ?? "", datasetId ?? "");
  const downloadDataset = useDownloadDataset(projectId ?? "");

  if (!projectId || !datasetId) {
    return <Navigate to="/projects" replace />;
  }

  if (datasetQuery.isPending) {
    return <DatasetDetailsSkeleton />;
  }

  if (datasetQuery.isError) {
    return (
      <div className="rounded-lg border bg-card px-6 py-14 text-center shadow-sm">
        <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle
            className="size-5 text-destructive"
            aria-hidden="true"
          />
        </span>

        <h1 className="mt-5 text-lg font-semibold">
          Dataset could not be loaded
        </h1>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          {datasetQuery.error.message}
        </p>

        <div className="mt-6 flex justify-center gap-3">
          <Button variant="outline" asChild>
            <Link to={`/projects/${projectId}`}>Back to project</Link>
          </Button>

          <Button
            disabled={datasetQuery.isFetching}
            onClick={() => {
              void datasetQuery.refetch();
            }}
          >
            <RefreshCw
              className={
                datasetQuery.isFetching ? "animate-spin" : undefined
              }
              aria-hidden="true"
            />
            Try again
          </Button>
        </div>
      </div>
    );
  }

  const dataset = datasetQuery.data;
  const status = dataset.status || "unknown";
  const statusLabel = status.replace(/_/g, " ");

  function handleDownload() {
    downloadDataset.mutate(dataset.id, {
      onSuccess: (url) => {
        const opened = window.open(
          url,
          "_blank",
          "noopener,noreferrer",
        );

        if (!opened) {
          window.location.assign(url);
        }

        toast.success("Download started.");
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
          <div className="flex min-w-0 items-start gap-3">
            <span className="flex size-12 shrink-0 items-center justify-center rounded-lg border bg-muted/50">
              <FileSpreadsheet
                className="size-6 text-muted-foreground"
                aria-hidden="true"
              />
            </span>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="wrap-break-word text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">
                  {dataset.original_filename}
                </h1>

                <Badge
                  variant={getStatusVariant(status)}
                  className="capitalize"
                >
                  {statusLabel}
                </Badge>
              </div>

              <p className="mt-2 text-sm text-muted-foreground">
                {getFileType(dataset)} ·{" "}
                {formatCount(dataset.row_count)} rows ·{" "}
                {formatCount(dataset.column_count)} columns · Updated{" "}
                {formatDate(dataset.updated_at).toLowerCase()}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <Button
              variant="outline"
              disabled={downloadDataset.isPending}
              onClick={handleDownload}
            >
              {downloadDataset.isPending ? (
                <LoaderCircle
                  className="animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Download aria-hidden="true" />
              )}
              {downloadDataset.isPending ? "Preparing…" : "Download"}
            </Button>

            <DatasetDetailsActions
              projectId={projectId}
              dataset={dataset}
            />
          </div>
        </div>

        {downloadDataset.isError && (
          <p role="alert" className="mt-4 text-sm text-destructive">
            {downloadDataset.error.message}
          </p>
        )}
      </header>

      <section aria-labelledby="overview-heading" className="space-y-4">
        <div>
          <h2
            id="overview-heading"
            className="text-lg font-semibold tracking-tight"
          >
            Dataset overview
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            A quick summary of this source file.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <OverviewMetric
            label="Rows"
            value={formatCount(dataset.row_count)}
            detail="Data rows"
          />
          <OverviewMetric
            label="Columns"
            value={formatCount(dataset.column_count)}
            detail="Dataset fields"
          />
          <OverviewMetric
            label="Size"
            value={formatSize(dataset.size_bytes)}
            detail="Stored file size"
          />
          <OverviewMetric
            label="Status"
            value={statusLabel}
            detail="Processing state"
          />
        </div>
      </section>

      <AnalysisComposer
        projectId={projectId}
        initialDatasetId={dataset.id}
      />

      <DatasetMetadata metadata={dataset.metadata} />
    </div>
  );
}
