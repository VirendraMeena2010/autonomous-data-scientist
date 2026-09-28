import {
  Activity,
  CircleCheck,
  Database,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";

import type { ProjectSummary as ProjectSummaryData } from "@/types/project";

interface ProjectSummaryProps {
  summary?: ProjectSummaryData;
  isLoading: boolean;
  error: Error | null;
}

interface Metric {
  label: string;
  value: string;
  description: string;
  icon: LucideIcon;
}

const numberFormatter = new Intl.NumberFormat();

function formatCount(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? numberFormatter.format(value)
    : "—";
}

function formatSuccessRate(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "—";
  }

  const percentage = value >= 0 && value <= 1 ? value * 100 : value;

  return `${new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 1,
  }).format(percentage)}%`;
}

export function ProjectSummary({
  summary,
  isLoading,
  error,
}: ProjectSummaryProps) {
  const metrics: Metric[] = [
    {
      label: "Datasets",
      value: formatCount(summary?.dataset_count),
      description: "Uploaded source files",
      icon: Database,
    },
    {
      label: "Analyses",
      value: formatCount(summary?.analysis_count),
      description: "Questions investigated",
      icon: ScanSearch,
    },
    {
      label: "Successful",
      value: formatCount(summary?.succeeded_count),
      description: "Completed analyses",
      icon: CircleCheck,
    },
    {
      label: "Success rate",
      value: formatSuccessRate(summary?.success_rate),
      description: "Across completed runs",
      icon: Activity,
    },
  ];

  return (
    <section aria-labelledby="summary-heading">
      <div className="mb-3 flex items-center justify-between gap-4">
        <h2
          id="summary-heading"
          className="text-sm font-semibold tracking-tight"
        >
          Summary
        </h2>

        {isLoading && (
          <span className="text-xs text-muted-foreground">Loading…</span>
        )}
      </div>

      {error && (
        <div
          role="status"
          className="rounded-lg border bg-card p-4 text-sm text-muted-foreground"
        >
          Summary unavailable: {error.message}
        </div>
      )}

      {!error && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map(({ label, value, description, icon: Icon }) => (
            <article
              key={label}
              className="rounded-lg border bg-card p-4 shadow-sm"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-medium text-muted-foreground">
                  {label}
                </p>
                <Icon
                  className="size-3.5 text-muted-foreground"
                  aria-hidden="true"
                />
              </div>

              {isLoading ? (
                <div
                  className="mt-4 h-8 w-20 animate-pulse rounded bg-muted"
                  aria-hidden="true"
                />
              ) : (
                <p className="mt-3 text-2xl font-semibold tracking-[-0.03em]">
                  {value}
                </p>
              )}

              <p className="mt-1 text-xs text-muted-foreground">
                {description}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
