import { Menu } from "lucide-react";

import { BrandMark } from "@/components/auth/brand-mark";
import { UserMenu } from "@/components/layout/user-menu";
import { Button } from "@/components/ui/button";

interface AppHeaderProps {
  pathname: string;
  onOpenNavigation: () => void;
}

function getPageLabel(pathname: string): string {
  if (pathname.includes("/datasets/")) {
    return "Dataset";
  }

  if (pathname.includes("/analyses/")) {
    return "Analysis";
  }

  if (pathname !== "/projects" && pathname.startsWith("/projects/")) {
    return "Project workspace";
  }

  return "Projects";
}

export function AppHeader({
  pathname,
  onOpenNavigation,
}: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur-sm sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="-ml-2 lg:hidden"
          aria-label="Open navigation"
          onClick={onOpenNavigation}
        >
          <Menu aria-hidden="true" />
        </Button>

        <BrandMark compact className="lg:hidden" />

        <div className="hidden items-center gap-2 text-sm sm:flex">
          <span className="text-muted-foreground">Workspace</span>
          <span className="text-muted-foreground/40">/</span>
          <span className="truncate font-medium text-foreground">
            {getPageLabel(pathname)}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="hidden text-xs text-muted-foreground md:inline">
          Data investigation workspace
        </span>

        <UserMenu
          compact
          placement="bottom"
          className="lg:hidden"
        />
      </div>
    </header>
  );
}
