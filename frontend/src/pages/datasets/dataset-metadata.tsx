import { Database } from "lucide-react";
import type { ReactNode } from "react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { JsonObject } from "@/types/dataset";

interface DatasetMetadataProps {
  metadata: JsonObject | null;
}

interface MetadataSectionDefinition {
  title: string;
  aliases: readonly string[];
}

interface FoundMetadata {
  key: string;
  value: unknown;
}

type MetadataRecord = Record<string, unknown>;

const METADATA_SECTIONS: readonly MetadataSectionDefinition[] = [
  {
    title: "Columns",
    aliases: ["columns", "column_names", "schema"],
  },
  {
    title: "Data types",
    aliases: ["dtypes", "data_types", "types"],
  },
  {
    title: "Missing values",
    aliases: [
      "missing_values",
      "missing_value_counts",
      "null_counts",
    ],
  },
  {
    title: "Unique values",
    aliases: ["unique_values", "unique_counts", "nunique"],
  },
  {
    title: "Statistics",
    aliases: ["statistics", "stats", "numeric_statistics", "summary"],
  },
];

function isRecord(value: unknown): value is MetadataRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === "string") {
    return value.trim().length > 0;
  }

  if (Array.isArray(value)) {
    return value.length > 0;
  }

  if (isRecord(value)) {
    return Object.keys(value).length > 0;
  }

  return true;
}

function isScalar(
  value: unknown,
): value is string | number | boolean | bigint {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    typeof value === "bigint"
  );
}

function formatScalar(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number") {
    return new Intl.NumberFormat().format(value);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "bigint") {
    return value.toString();
  }

  return "—";
}

function formatValue(value: unknown): string {
  if (!hasValue(value)) {
    return "Not provided";
  }

  if (Array.isArray(value)) {
    if (value.every(isScalar)) {
      return value.map(formatScalar).join(", ");
    }

    return `${value.length} ${value.length === 1 ? "record" : "records"}`;
  }

  if (isRecord(value)) {
    return `${Object.keys(value).length} fields`;
  }

  return formatScalar(value);
}

function getRecordArray(value: unknown): MetadataRecord[] | null {
  if (!Array.isArray(value) || value.length === 0) {
    return null;
  }

  if (!value.every(isRecord)) {
    return null;
  }

  return value;
}

function humanizeKey(key: string): string {
  const knownKeys: Record<string, string> = {
    name: "Name",
    column: "Column",
    type: "Type",
    dtype: "Data type",
    missing: "Missing",
    missing_values: "Missing values",
    null_count: "Null count",
    unique: "Unique",
    unique_values: "Unique values",
    count: "Count",
    min: "Minimum",
    max: "Maximum",
    mean: "Mean",
    median: "Median",
    std: "Standard deviation",
    stddev: "Standard deviation",
  };

  return (
    knownKeys[key.toLowerCase()] ??
    key
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

function findMetadataValue(
  metadata: MetadataRecord,
  aliases: readonly string[],
): FoundMetadata | null {
  for (const alias of aliases) {
    const value = metadata[alias];

    if (hasValue(value)) {
      return { key: alias, value };
    }
  }

  return null;
}

function MetadataTable({ rows }: { rows: MetadataRecord[] }) {
  const visibleRows = rows.slice(0, 20);
  const columns = Array.from(
    new Set(visibleRows.flatMap((row) => Object.keys(row))),
  ).slice(0, 8);

  if (columns.length === 0) {
    return <p className="text-sm text-muted-foreground">No details provided.</p>;
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="bg-muted/50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  scope="col"
                  className="whitespace-nowrap px-3 py-2.5 text-xs font-medium text-muted-foreground"
                >
                  {humanizeKey(column)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y">
            {visibleRows.map((row, rowIndex) => (
              <tr key={`${rowIndex}-${columns.join("-")}`}>
                {columns.map((column) => (
                  <td
                    key={column}
                    className="max-w-[240px] truncate px-3 py-2.5 text-sm"
                    title={formatValue(row[column])}
                  >
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > visibleRows.length && (
        <p className="text-xs text-muted-foreground">
          Showing the first {visibleRows.length} of {rows.length} records.
        </p>
      )}
    </div>
  );
}

function MetadataValue({
  value,
  depth = 0,
}: {
  value: unknown;
  depth?: number;
}): ReactNode {
  const records = getRecordArray(value);

  if (records) {
    return <MetadataTable rows={records} />;
  }

  if (isRecord(value)) {
    const entries = Object.entries(value).filter(([, entry]) =>
      hasValue(entry),
    );

    if (depth >= 2) {
      return (
        <p className="text-sm text-muted-foreground">
          {formatValue(value)}
        </p>
      );
    }

    return (
      <dl className="grid gap-2 sm:grid-cols-2">
        {entries.slice(0, 12).map(([key, entry]) => (
          <div
            key={key}
            className="rounded-md border bg-muted/20 px-3 py-2.5"
          >
            <dt className="text-xs text-muted-foreground">
              {humanizeKey(key)}
            </dt>
            <dd className="mt-1 text-sm">
              <MetadataValue value={entry} depth={depth + 1} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  if (Array.isArray(value) && value.every(isScalar)) {
    return (
      <p className="break-words text-sm leading-6">
        {value.map(formatScalar).join(", ")}
      </p>
    );
  }

  return (
    <p className="break-words text-sm leading-6">
      {formatValue(value)}
    </p>
  );
}

function MetadataSection({
  title,
  found,
}: {
  title: string;
  found: FoundMetadata;
}) {
  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardHeader className="border-b px-5 py-4">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>

      <CardContent className="p-5">
        <MetadataValue value={found.value} />
      </CardContent>
    </Card>
  );
}

export function DatasetMetadata({ metadata }: DatasetMetadataProps) {
  if (!metadata || Object.keys(metadata).length === 0) {
    return (
      <section aria-labelledby="metadata-heading" className="space-y-4">
        <div>
          <h2
            id="metadata-heading"
            className="text-lg font-semibold tracking-tight"
          >
            Dataset metadata
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Structural information returned by the analysis service.
          </p>
        </div>

        <Card className="border-dashed py-10 shadow-sm">
          <CardContent className="flex flex-col items-center px-6 text-center">
            <span className="flex size-11 items-center justify-center rounded-xl border bg-muted/50">
              <Database
                className="size-5 text-muted-foreground"
                aria-hidden="true"
              />
            </span>

            <h3 className="mt-4 text-sm font-medium">
              Metadata not available yet
            </h3>

            <p className="mt-1 max-w-md text-sm leading-6 text-muted-foreground">
              Dataset details will appear here after metadata is available.
            </p>
          </CardContent>
        </Card>
      </section>
    );
  }

  const usedKeys = new Set<string>();
  const foundSections = METADATA_SECTIONS.flatMap((section) => {
    const found = findMetadataValue(metadata, section.aliases);

    if (!found) {
      return [];
    }

    usedKeys.add(found.key);

    return [{ title: section.title, found }];
  });

  const additionalEntries = Object.entries(metadata).filter(
    ([key, value]) => !usedKeys.has(key) && hasValue(value),
  );

  const hasAdditionalMetadata = additionalEntries.length > 0;

  return (
    <section aria-labelledby="metadata-heading" className="space-y-4">
      <div>
        <h2
          id="metadata-heading"
          className="text-lg font-semibold tracking-tight"
        >
          Dataset metadata
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Structural information returned by the analysis service.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {foundSections.map(({ title, found }) => (
          <MetadataSection
            key={title}
            title={title}
            found={found}
          />
        ))}

        {hasAdditionalMetadata && (
          <Card className="gap-0 py-0 shadow-sm xl:col-span-2">
            <CardHeader className="border-b px-5 py-4">
              <CardTitle className="text-sm">
                Additional metadata
              </CardTitle>
            </CardHeader>

            <CardContent className="p-5">
              <dl className="grid gap-2 sm:grid-cols-2">
                {additionalEntries.slice(0, 16).map(([key, value]) => (
                  <div
                    key={key}
                    className="rounded-md border bg-muted/20 px-3 py-2.5"
                  >
                    <dt className="text-xs text-muted-foreground">
                      {humanizeKey(key)}
                    </dt>
                    <dd className="mt-1 text-sm">
                      <MetadataValue value={value} />
                    </dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  );
}
