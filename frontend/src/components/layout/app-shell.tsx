import {  useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { MobileNavigation } from "@/components/layout/mobile-navigation";

export function AppShell() {
  const location = useLocation();
  const [navigationOpen, setNavigationOpen] = useState(false);


  useEffect(() => {
    setNavigationOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex min-h-dvh bg-background">
      <a
        href="#main-content"
        className="sr-only z-100 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-lg focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to content
      </a>

      <aside className="sticky top-0 hidden h-dvh w-62 shrink-0 border-r lg:block">
        <AppSidebar />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader
          pathname={location.pathname}
          onOpenNavigation={() => {
            setNavigationOpen(true);
          }}
        />

        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 flex-1 outline-none"
        >
          <div className="mx-auto w-full max-w-360 px-4 py-7 sm:px-6 sm:py-9 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>

      <MobileNavigation
        open={navigationOpen}
        onOpenChange={setNavigationOpen}
      />
    </div>
  );
}
