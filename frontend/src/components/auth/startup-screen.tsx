import { BrandMark } from "@/components/auth/brand-mark";

export function StartupScreen() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-background px-6">
      <div className="flex flex-col items-center gap-8">
        <BrandMark />

        <div
          className="flex items-center gap-1.5"
          role="status"
          aria-label="Restoring your workspace"
        >
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/40" />
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/60 [animation-delay:150ms]" />
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
        </div>

        <p className="sr-only">Restoring your authenticated workspace…</p>
      </div>
    </main>
  );
}
