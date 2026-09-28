import { Folder, Network } from "lucide-react";
import { NavLink } from "react-router-dom";

import { BrandMark } from "@/components/auth/brand-mark";
import { UserMenu } from "@/components/layout/user-menu";
import { cn } from "@/lib/utils";

interface AppSidebarProps {
  onNavigate?: () => void;
  className?: string;
}

export function AppSidebar({
  onNavigate,
  className,
}: AppSidebarProps) {
  return (
    <div className={cn("flex h-full flex-col bg-card", className)}>
      <div className="flex h-16 shrink-0 items-center border-b px-5">
        <BrandMark />
      </div>

      <nav
        className="flex-1 p-3"
        aria-label="Primary navigation"
      >
        <p className="mb-2 px-2 pt-2 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Workspace
        </p>

        <NavLink
          to="/projects"
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex h-9 items-center gap-3 rounded-md px-2.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-secondary text-secondary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )
          }
        >
          <Folder className="size-4" aria-hidden="true" />
          Projects
        </NavLink>
      </nav>

      <div className="border-t p-3">
        <div className="mb-3 flex items-center gap-2 px-2 text-[11px] leading-4 text-muted-foreground">
          <Network className="size-3.5 shrink-0" aria-hidden="true" />
          Evidence-led analysis
        </div>

        <UserMenu placement="top" onLogout={onNavigate} />
      </div>
    </div>
  );
}
