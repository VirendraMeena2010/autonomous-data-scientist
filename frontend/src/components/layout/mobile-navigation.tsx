import { X } from "lucide-react";
import { useEffect, useRef } from "react";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { Button } from "@/components/ui/button";

interface MobileNavigationProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MobileNavigation({
  open,
  onOpenChange,
}: MobileNavigationProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";

    const focusFrame = window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus();
    });

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [onOpenChange, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button
        type="button"
        className="absolute inset-0 cursor-default bg-slate-950/35 backdrop-blur-[2px]"
        aria-label="Close navigation"
        onClick={() => {
          onOpenChange(false);
        }}
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-navigation-title"
        className="relative h-full w-71.5 max-w-[85vw] border-r bg-card shadow-xl"
      >
        <h2 id="mobile-navigation-title" className="sr-only">
          Application navigation
        </h2>

        <Button
          ref={closeButtonRef}
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-3 top-3 z-10"
          aria-label="Close navigation"
          onClick={() => {
            onOpenChange(false);
          }}
        >
          <X aria-hidden="true" />
        </Button>

        <AppSidebar
          onNavigate={() => {
            onOpenChange(false);
          }}
          className="h-full"
        />
      </aside>
    </div>
  );
}
