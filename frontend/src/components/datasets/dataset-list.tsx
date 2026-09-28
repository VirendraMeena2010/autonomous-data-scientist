import {
  AlertCircle,
  ArrowUpRight,
  FileSpreadsheet,
  RefreshCw,
  UploadCloud,
} from "lucide-react";
import { Link } from "react-router-dom";

import { DatasetUploadDialog } from "@/components/datasets/dataset-upload-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDatasets } from "@/hooks/use-datasets";
import type { Dataset } from "@/types/dataset";

interface DatasetListProps {
  projectId: string;
}

const numberFormatter = new Intl.NumberFormat();

function formatCount(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? numberFormatter.format(value)
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

function formatUpdatedAt(value: string | undefined): string {
  if (!value) {
    return "Recently updated";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Recently updated";
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

function DatasetStatus({ dataset }: { dataset: Dataset }) {
  const status = dataset.status.toLowerCase();

  const variant =
    status === "failed"
      ? "destructive"
      : status === "ready"
        ? "secondary"
        : "outline";

  return (
    <Badge variant={variant} className="capitalize">
      {dataset.status}
    </Badge>
  );
}

function DatasetListSkeleton() {
  return (
    <div className="space-y-3" aria-label="Loading datasets">
      {Array.from({ length: 3 }, (_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-lg border bg-card p-4 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-md bg-muted" />
            <div className="flex-1">
              <div className="h-4 w-48 max-w-full rounded bg-muted" />
              <div className="mt-2 h-3 w-64 max-w-full rounded bg-muted/70" />
            </div>
            <div className="h-5 w-16 rounded-full bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DatasetList({ projectId }: DatasetListProps) {
  const datasetsQuery = useDatasets(projectId);

  return (
    <section aria-labelledby="datasets-heading" className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2
            id="datasets-heading"
            className="text-lg font-semibold tracking-tight"
          >
            Datasets
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Source files available for autonomous investigation.
          </p>
        </div>
      </div>

      {datasetsQuery.isPending && <DatasetListSkeleton />}

      {datasetsQuery.isError && (
        <div className="rounded-lg border bg-card p-8 text-center shadow-sm">
          <span className="mx-auto flex size-10 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle
              className="size-5 text-destructive"
              aria-hidden="true"
            />
          </span>

          <h3 className="mt-4 text-base font-medium">
            Datasets could not be loaded
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            {datasetsQuery.error.message}
          </p>

          <Button
            className="mt-5"
            variant="outline"
            disabled={datasetsQuery.isFetching}
            onClick={() => {
              void datasetsQuery.refetch();
            }}
          >
            <RefreshCw
              className={
                datasetsQuery.isFetching ? "animate-spin" : undefined
              }
              aria-hidden="true"
            />
            {datasetsQuery.isFetching ? "Retrying…" : "Try again"}
          </Button>
        </div>
      )}

      {datasetsQuery.isSuccess && datasetsQuery.data.length === 0 && (
        <div className="rounded-lg border border-dashed bg-card px-6 py-14 text-center shadow-sm">
          <span className="mx-auto flex size-12 items-center justify-center rounded-xl border bg-muted/50">
            <FileSpreadsheet
              className="size-5 text-muted-foreground"
              aria-hidden="true"
            />
          </span>

          <h3 className="mt-5 text-lg font-semibold tracking-tight">
            No datasets uploaded
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            Upload a CSV file to make it available for analysis.
          </p>

          <div className="mt-6">
            <DatasetUploadDialog projectId={projectId}>
              <Button>
                <UploadCloud aria-hidden="true" />
                Upload Dataset
              </Button>
            </DatasetUploadDialog>
          </div>
        </div>
      )}

      {datasetsQuery.isSuccess && datasetsQuery.data.length > 0 && (
        <ul className="space-y-3" aria-label="Uploaded datasets">
          {datasetsQuery.data.map((dataset) => (
            <li key={dataset.id}>
              <Link
                to={`/projects/${projectId}/datasets/${dataset.id}`}
                className="group flex items-center gap-3 rounded-lg border bg-card p-4 shadow-sm outline-none transition-colors hover:border-muted-foreground/30 hover:bg-card/80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background sm:gap-4"
              >
                <span className="flex size-10 shrink-0 items-center justify-center rounded-md border bg-muted/50">
                  <FileSpreadsheet
                    className="size-5 text-muted-foreground"
                    aria-hidden="true"
                  />
                </span>

                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">
                    {dataset.original_filename}
                  </span>

                  <span className="mt-1 block truncate text-xs text-muted-foreground">
                    {formatCount(dataset.row_count)} rows ·{" "}
                    {formatCount(dataset.column_count)} columns ·{" "}
                    {formatSize(dataset.size_bytes)}
                  </span>
                </span>

                <span className="hidden shrink-0 text-xs text-muted-foreground sm:block">
                  {formatUpdatedAt(dataset.updated_at)}
                </span>

                <DatasetStatus dataset={dataset} />

                <ArrowUpRight
                  className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
