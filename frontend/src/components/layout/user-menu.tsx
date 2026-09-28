import { ChevronUp, LoaderCircle, LogOut } from "lucide-react";
import { useRef } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

interface UserMenuProps {
  compact?: boolean;
  placement?: "top" | "bottom";
  onLogout?: () => void;
  className?: string;
}

export function UserMenu({
  compact = false,
  placement = "top",
  onLogout,
  className,
}: UserMenuProps) {
  const { user, logout, isLoggingOut } = useAuth();
  const detailsRef = useRef<HTMLDetailsElement>(null);

  const displayName = user?.name?.trim() || "Account";
  const email = user?.email ?? "";

  const initials = user?.name?.trim()
    ? user.name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase()
    : (email[0] ?? "U").toUpperCase();

  async function handleLogout() {
    detailsRef.current?.removeAttribute("open");

    try {
      await logout();
      onLogout?.();
      toast.success("Signed out successfully.");
    } catch (error: unknown) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Unable to sign out. Please try again.",
      );
    }
  }

  return (
    <details ref={detailsRef} className={cn("group relative", className)}>
      <summary
        className={cn(
          "flex list-none items-center rounded-md transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring [&::-webkit-details-marker]:hidden",
          compact
            ? "size-9 justify-center"
            : "w-full gap-3 px-2 py-2",
        )}
        aria-label="Open user menu"
      >
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-[11px] font-semibold text-secondary-foreground">
          {initials}
        </span>

        {!compact && (
          <>
            <span className="min-w-0 flex-1 text-left">
              <span className="block truncate text-sm font-medium leading-5">
                {displayName}
              </span>
              <span className="block truncate text-xs leading-4 text-muted-foreground">
                {email}
              </span>
            </span>

            <ChevronUp
              className="size-3.5 shrink-0 text-muted-foreground"
              aria-hidden="true"
            />
          </>
        )}
      </summary>

      <div
        className={cn(
          "absolute z-50 w-56 rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-lg",
          placement === "top"
            ? "bottom-[calc(100%+8px)] left-0"
            : "right-0 top-[calc(100%+8px)]",
        )}
      >
        <div className="border-b px-2.5 py-2.5">
          <p className="truncate text-sm font-medium">{displayName}</p>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {email}
          </p>
        </div>

        <Button
          type="button"
          variant="ghost"
          className="mt-1 w-full justify-start text-sm font-normal"
          disabled={isLoggingOut}
          onClick={() => {
            void handleLogout();
          }}
        >
          {isLoggingOut ? (
            <LoaderCircle className="animate-spin" aria-hidden="true" />
          ) : (
            <LogOut aria-hidden="true" />
          )}
          {isLoggingOut ? "Signing out…" : "Sign out"}
        </Button>
      </div>
    </details>
  );
}
