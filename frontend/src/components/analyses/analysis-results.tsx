import {
  BarChart3,
  ClipboardList,
  FileText,
  Flag,
  Info,
  ListChecks,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type {
  Analysis,
  AnalysisPlan,
  AnalysisProfile,
  AnalysisQuality,
  AnalysisReport,
  Finding,
} from "@/types/analysis";

interface AnalysisResultsProps {
  analysis: Analysis;
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function asText(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const text = value.trim();

  return text || null;
}

function firstText(
  value: unknown,
  keys: readonly string[],
): string | null {
  if (!isRecord(value)) {
    return null;
  }

  for (const key of keys) {
    const text = asText(value[key]);

    if (text) {
      return text;
    }
  }

  return null;
}

function humanizeKey(key: string): string {
  return key
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not provided";
  }

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

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "None";
    }

    if (value.every((item) => typeof item === "string")) {
      return value.join(", ");
    }

    return `${value.length} items`;
  }

  if (isRecord(value)) {
    return `${Object.keys(value).length} fields`;
  }

  return String(value);
}

function ValueView({
  value,
  depth = 0,
}: {
  value: unknown;
  depth?: number;
}): ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">Not provided</span>;
  }

  if (typeof value === "string") {
    return <span className="whitespace-pre-wrap">{value}</span>;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean" ||
    typeof value === "bigint"
  ) {
    return <span>{formatValue(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-muted-foreground">None</span>;
    }

    if (value.every((item) => typeof item === "string")) {
      return (
        <ul className="list-disc space-y-1 pl-5">
          {value.map((item, index) => (
            <li key={`${String(item)}-${index}`}>{item}</li>
          ))}
        </ul>
      );
    }

    if (value.every(isRecord)) {
      const firstRow = value[0] as UnknownRecord;
      const columns = Object.keys(firstRow).slice(0, 6);

      if (columns.length === 0) {
        return (
          <span className="text-muted-foreground">
            No tabular details returned.
          </span>
        );
      }

      return (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full min-w-120 text-left text-sm">
            <thead className="bg-muted/50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    scope="col"
                    className="whitespace-nowrap px-3 py-2 text-xs font-medium text-muted-foreground"
                  >
                    {humanizeKey(column)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {value.slice(0, 20).map((row, rowIndex) => {
                const record = row as UnknownRecord;

                return (
                  <tr key={`row-${rowIndex}`}>
                    {columns.map((column) => (
                      <td
                        key={column}
                        className="max-w-55 truncate px-3 py-2.5"
                        title={formatValue(record[column])}
                      >
                        {formatValue(record[column])}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
    }

    return (
      <ul className="list-disc space-y-1 pl-5">
        {value.slice(0, 20).map((item, index) => (
          <li key={`item-${index}`}>
            <ValueView value={item} depth={depth + 1} />
          </li>
        ))}
      </ul>
    );
  }

  if (isRecord(value)) {
    const entries = Object.entries(value).filter(
      ([, entry]) => entry !== null && entry !== undefined,
    );

    if (depth >= 2) {
      return (
        <span className="text-muted-foreground">
          {formatValue(value)}
        </span>
      );
    }

    return (
      <dl className="grid gap-2 sm:grid-cols-2">
        {entries.slice(0, 16).map(([key, entry]) => (
          <div
            key={key}
            className="rounded-md border bg-muted/20 px-3 py-2.5"
          >
            <dt className="text-xs text-muted-foreground">
              {humanizeKey(key)}
            </dt>
            <dd className="mt-1 text-sm leading-6">
              <ValueView value={entry} depth={depth + 1} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return <span>{String(value)}</span>;
}

interface ResultCardProps {
  title: string;
  description: string;
  icon: typeof Info;
  children: ReactNode;
}

function ResultCard({
  title,
  description,
  icon: Icon,
  children,
}: ResultCardProps) {
  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardHeader className="border-b px-5 py-4 sm:px-6">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
            <Icon
              className="size-4 text-muted-foreground"
              aria-hidden="true"
            />
          </span>

          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <p className="mt-1 text-sm leading-5 text-muted-foreground">
              {description}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 sm:p-6">{children}</CardContent>
    </Card>
  );
}

function EmptyResult({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed bg-muted/20 px-4 py-5 text-sm leading-6 text-muted-foreground">
      {message}
    </div>
  );
}

function getFindingText(finding: Finding): string | null {
  return firstText(finding, [
    "finding",
    "title",
    "summary",
    "statement",
    "conclusion",
    "insight",
  ]);
}

function ExecutiveSummary({ analysis }: AnalysisResultsProps) {
  const summary = firstText(analysis.report, [
    "executive_summary",
    "summary",
    "overview",
    "abstract",
  ]);

  const findingTexts = analysis.findings
    .filter(isRecord)
    .map((finding) => getFindingText(finding as Finding))
    .filter((text): text is string => Boolean(text))
    .slice(0, 3);

  return (
    <ResultCard
      title="Executive Summary"
      description="The most important conclusions returned by the analysis."
      icon={BarChart3}
    >
      {summary || findingTexts.length > 0 ? (
        <div className="space-y-5">
          {summary && (
            <p className="text-[15px] leading-7 text-foreground/90">
              {summary}
            </p>
          )}

          {findingTexts.length > 0 && (
            <div className="border-l-2 border-primary/30 pl-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Highlighted findings
              </p>

              <ul className="mt-3 space-y-2">
                {findingTexts.map((finding, index) => (
                  <li
                    key={`${finding}-${index}`}
                    className="text-sm leading-6"
                  >
                    {finding}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <EmptyResult message="No executive summary was included in the response." />
      )}
    </ResultCard>
  );
}

function Findings({ analysis }: AnalysisResultsProps) {
  const findings = analysis.findings.filter(isRecord) as Finding[];

  return (
    <ResultCard
      title="Key Findings"
      description="Conclusions and supporting evidence returned by the analysis."
      icon={Flag}
    >
      {findings.length === 0 ? (
        <EmptyResult message="No findings were included in the response." />
      ) : (
        <ol className="space-y-6">
          {findings.map((finding, index) => {
            const title = getFindingText(finding);
            const evidence = finding.evidence;
            const explanation =
              asText(finding.explanation) ?? asText(finding.detail);
            const confidence = finding.confidence;
            const impact = finding.impact;

            return (
              <li
                key={`${finding.id ?? "finding"}-${index}`}
                className="grid gap-3 sm:grid-cols-[2.5rem_1fr]"
              >
                <span className="font-mono text-xs text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <div className="min-w-0 border-b pb-6 last:border-0 last:pb-0">
                  <h3 className="text-sm font-semibold leading-6">
                    {title ?? "Untitled finding"}
                  </h3>

                  {explanation && (
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {explanation}
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap gap-2">
                    {confidence !== undefined &&
                      confidence !== null && (
                      <Badge variant="outline">
                        Confidence: {formatValue(confidence)}
                      </Badge>
                    )}

                    {impact && (
                      <Badge variant="secondary">{impact}</Badge>
                    )}
                  </div>

                  {evidence !== undefined &&
                    evidence !== null && (
                      <div className="mt-4 rounded-md border bg-muted/25 p-3">
                        <p className="text-xs font-medium text-muted-foreground">
                          Evidence
                        </p>
                        <div className="mt-2 text-sm leading-6">
                          <ValueView value={evidence} />
                        </div>
                      </div>
                    )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </ResultCard>
  );
}

function DataQuality({ quality }: { quality: AnalysisQuality }) {
  return (
    <ResultCard
      title="Data Quality"
      description="Quality observations returned with this analysis."
      icon={ShieldCheck}
    >
      {quality ? (
        <div className="text-sm leading-6">
          <ValueView value={quality} />
        </div>
      ) : (
        <EmptyResult message="No data quality information was returned." />
      )}
    </ResultCard>
  );
}

function DatasetProfile({ profile }: { profile: AnalysisProfile }) {
  return (
    <ResultCard
      title="Dataset Profile"
      description="Structural information observed during the analysis."
      icon={ClipboardList}
    >
      {profile ? (
        <div className="text-sm leading-6">
          <ValueView value={profile} />
        </div>
      ) : (
        <EmptyResult message="No dataset profile was returned." />
      )}
    </ResultCard>
  );
}

function AnalysisPlan({ plan }: { plan: AnalysisPlan }) {
  return (
    <ResultCard
      title="Analysis Plan"
      description="The investigation approach returned by the backend."
      icon={ListChecks}
    >
      {plan ? (
        <div className="text-sm leading-6">
          <ValueView value={plan} />
        </div>
      ) : (
        <EmptyResult message="No analysis plan was returned." />
      )}
    </ResultCard>
  );
}

function ReportDocument({ report }: { report: AnalysisReport }) {
  const text =
    typeof report === "string"
      ? report
      : firstText(report, ["content", "markdown", "text", "body"]);

  if (text) {
    const blocks = text.split(/\n\s*\n/).filter(Boolean);

    return (
      <article className="max-w-3xl space-y-5">
        {blocks.map((block, index) => {
          const lines = block.split("\n");
          const firstLine = lines[0]?.trim() ?? "";
          const isHeading = /^#{1,3}\s/.test(firstLine);
          const isList = lines.every((line) =>
            /^\s*[-*]\s+/.test(line),
          );

          if (isList) {
            return (
              <ul
                key={`report-${index}`}
                className="list-disc space-y-1 pl-5"
              >
                {lines.map((line, lineIndex) => (
                  <li key={`report-${index}-${lineIndex}`}>
                    {line.replace(/^\s*[-*]\s+/, "")}
                  </li>
                ))}
              </ul>
            );
          }

          if (isHeading) {
            return (
              <h3
                key={`report-${index}`}
                className="text-base font-semibold tracking-tight"
              >
                {firstLine.replace(/^#{1,3}\s/, "")}
              </h3>
            );
          }

          return (
            <p
              key={`report-${index}`}
              className="whitespace-pre-wrap text-sm leading-7 text-foreground/85"
            >
              {block}
            </p>
          );
        })}
      </article>
    );
  }

  if (isRecord(report)) {
    return <ValueView value={report} />;
  }

  return <EmptyResult message="No report was returned for this analysis." />;
}

function Report({ report }: { report: AnalysisReport }) {
  return (
    <ResultCard
      title="Report"
      description="The generated analytical report."
      icon={FileText}
    >
      <ReportDocument report={report} />
    </ResultCard>
  );
}

export function AnalysisResults({ analysis }: AnalysisResultsProps) {
  return (
    <div className="space-y-5">
      <ExecutiveSummary analysis={analysis} />
      <Findings analysis={analysis} />
      <DataQuality quality={analysis.quality} />
      <DatasetProfile profile={analysis.profile} />
      <AnalysisPlan plan={analysis.plan} />
      <Report report={analysis.report} />
    </div>
  );
}
