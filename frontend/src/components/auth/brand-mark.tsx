import { Database } from "lucide-react";

import { cn } from "@/lib/utils";

interface BrandMarkProps {
  inverted?: boolean;
  compact?: boolean;
  className?: string;
}

export function BrandMark({
  inverted = false,
  compact = false,
  className,
}: BrandMarkProps) {
  return (
    <div
      className={cn("flex items-center gap-3", compact && "gap-2.5", className)}
      role="img"
      aria-label="ADS — Autonomous Data Scientist"
    >
      <span
        aria-hidden="true"
        className={cn(
          "relative flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-xl border shadow-sm",
          inverted
            ? "border-white/15 bg-white/10"
            : "border-slate-950/10 bg-slate-900",
        )}
      >
        <Database
          className={cn(
            "absolute left-2.5 top-2.5 size-5",
            inverted ? "text-slate-100" : "text-white",
          )}
        />

        <span className="absolute bottom-2.5 right-2.5 flex items-end gap-0.5">
          <span
            className={cn(
              "h-1 w-1 rounded-sm",
              inverted ? "bg-slate-300" : "bg-slate-400",
            )}
          />
          <span
            className={cn(
              "h-1.5 w-1 rounded-sm",
              inverted ? "bg-slate-300" : "bg-slate-400",
            )}
          />
          <span
            className={cn(
              "h-2 w-1 rounded-sm",
              inverted ? "bg-slate-100" : "bg-white",
            )}
          />
        </span>
      </span>

      <span className="flex flex-col">
        <span
          className={cn(
            "text-sm font-semibold tracking-[-0.02em]",
            inverted ? "text-white" : "text-foreground",
          )}
        >
          ADS
        </span>

        {!compact && (
          <span
            className={cn(
              "mt-0.5 text-[11px] leading-4",
              inverted ? "text-slate-400" : "text-muted-foreground",
            )}
          >
            Autonomous Data Scientist
          </span>
        )}
      </span>
    </div>
  );
}
