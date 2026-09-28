import {
  ArrowRight,
  FileSpreadsheet,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useCreateAnalysis } from "@/hooks/use-analyses";
import { useDatasets } from "@/hooks/use-datasets";

interface AnalysisComposerProps {
  projectId: string;
  initialDatasetId?: string;
}

const SUGGESTED_QUESTIONS = [
  "What are the main factors affecting profit?",
  "Which products generate the most revenue?",
  "Find unusual patterns in the data.",
  "What data quality problems should I know about?",
  "Which customer segments perform best?",
  "Identify important trends.",
] as const;

export function AnalysisComposer({
  projectId,
  initialDatasetId,
}: AnalysisComposerProps) {
  const navigate = useNavigate();
  const datasetsQuery = useDatasets(projectId);
  const createAnalysis = useCreateAnalysis(projectId);

  const [selectedDatasetId, setSelectedDatasetId] = useState(
    initialDatasetId ?? "",
  );
  const [question, setQuestion] = useState("");

  useEffect(() => {
    if (initialDatasetId) {
      setSelectedDatasetId(initialDatasetId);
    }
  }, [initialDatasetId]);

  const datasets = datasetsQuery.data ?? [];

  const selectedDataset = useMemo(
    () =>
      datasets.find((dataset) => dataset.id === selectedDatasetId) ?? null,
    [datasets, selectedDatasetId],
  );

  const trimmedQuestion = question.trim();
  const canSubmit =
    Boolean(selectedDatasetId) &&
    trimmedQuestion.length >= 5 &&
    !createAnalysis.isPending;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedDatasetId) {
      toast.error("Choose a dataset before running an analysis.");
      return;
    }

    if (trimmedQuestion.length < 5) {
      toast.error("Enter a clear analytical question.");
      return;
    }

    createAnalysis.mutate(
      {
        dataset_id: selectedDatasetId,
        question: trimmedQuestion,
      },
      {
        onSuccess: (createdAnalysis) => {
          toast.success("Analysis created.");
          void navigate(
            `/projects/${projectId}/analyses/${createdAnalysis.id}`,
          );
        },
      },
    );
  }

  return (
    <section
      aria-labelledby="analysis-composer-heading"
      className="overflow-hidden rounded-xl border bg-card shadow-sm"
    >
      <div className="border-b px-5 py-5 sm:px-6">
        <div className="flex items-center gap-2">
          <Sparkles
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <h2
            id="analysis-composer-heading"
            className="text-base font-semibold tracking-tight"
          >
            Ask your dataset
          </h2>
        </div>

        <p className="mt-1.5 text-sm leading-6 text-muted-foreground">
          Frame a question and let the autonomous analysis service investigate
          the available evidence.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-5 p-5 sm:p-6"
        noValidate
      >
        <div className="space-y-2">
          <label
            htmlFor="analysis-question"
            className="text-sm font-medium"
          >
            What would you like to understand?
          </label>

          <Textarea
            id="analysis-question"
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
            }}
            placeholder="What are the main factors affecting profit?"
            className="min-h-36 resize-y text-[15px] leading-7"
            maxLength={2000}
            disabled={createAnalysis.isPending}
            aria-describedby="analysis-question-help"
          />

          <div
            id="analysis-question-help"
            className="flex items-center justify-between gap-4 text-xs text-muted-foreground"
          >
            <span>Be as specific or open-ended as you need.</span>
            <span>{question.length}/2000</span>
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="analysis-dataset" className="text-sm font-medium">
            Dataset
          </label>

          {datasetsQuery.isPending ? (
            <div className="flex h-10 animate-pulse items-center gap-2 rounded-md border bg-muted/40 px-3 text-sm text-muted-foreground">
              <LoaderCircle
                className="size-4 animate-spin"
                aria-hidden="true"
              />
              Loading datasets…
            </div>
          ) : datasets.length === 0 ? (
            <div className="rounded-md border border-dashed bg-muted/20 px-4 py-4 text-sm leading-6 text-muted-foreground">
              Upload a CSV dataset before running an analysis.
            </div>
          ) : (
            <div className="relative">
              <FileSpreadsheet
                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />

              <select
                id="analysis-dataset"
                value={selectedDatasetId}
                onChange={(event) => {
                  setSelectedDatasetId(event.target.value);
                }}
                disabled={
                  createAnalysis.isPending || Boolean(initialDatasetId)
                }
                className="h-10 w-full appearance-none rounded-md border border-input bg-background py-2 pl-10 pr-9 text-sm shadow-xs outline-none transition-colors hover:border-muted-foreground/50 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <option value="" disabled>
                  Select a dataset
                </option>

                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.original_filename}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedDataset && (
            <p className="text-xs text-muted-foreground">
              {selectedDataset.row_count?.toLocaleString() ?? "Unknown"} rows ·{" "}
              {selectedDataset.column_count?.toLocaleString() ?? "Unknown"}{" "}
              columns · {selectedDataset.status}
            </p>
          )}

          {datasetsQuery.isError && (
            <p role="alert" className="text-xs text-destructive">
              {datasetsQuery.error.message}
            </p>
          )}
        </div>

        <div className="space-y-3">
          <p className="text-xs font-medium text-muted-foreground">
            Suggested questions
          </p>

          <div className="grid gap-2 sm:grid-cols-2">
            {SUGGESTED_QUESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="rounded-md border bg-background px-3 py-2.5 text-left text-xs leading-5 text-muted-foreground outline-none transition-colors hover:border-muted-foreground/30 hover:bg-muted/40 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={createAnalysis.isPending}
                onClick={() => {
                  setQuestion(suggestion);
                  document.getElementById("analysis-question")?.focus();
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        {createAnalysis.isError && (
          <div
            role="alert"
            className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm leading-5 text-destructive"
          >
            {createAnalysis.error.message}
          </div>
        )}

        <div className="flex flex-col-reverse gap-3 border-t pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-5 text-muted-foreground">
            Results appear when the backend analysis completes.
          </p>

          <Button
            type="submit"
            disabled={!canSubmit}
            className="w-full sm:w-auto"
          >
            {createAnalysis.isPending ? (
              <LoaderCircle
                className="animate-spin"
                aria-hidden="true"
              />
            ) : null}
            {createAnalysis.isPending
              ? "Starting analysis…"
              : "Run Analysis"}
            {!createAnalysis.isPending && (
              <ArrowRight aria-hidden="true" />
            )}
          </Button>
        </div>
      </form>
    </section>
  );
}
