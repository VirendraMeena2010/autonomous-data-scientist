import { Navigate, Outlet, useLocation } from "react-router-dom";

import { StartupScreen } from "@/components/auth/startup-screen";
import { useAuth } from "@/hooks/use-auth";

export function RequireAuthentication() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <StartupScreen />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: {
            pathname: location.pathname,
            search: location.search,
          },
        }}
      />
    );
  }

  return <Outlet />;
}

export function RequireGuest() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <StartupScreen />;
  }

  if (isAuthenticated) {
    return <Navigate to="/projects" replace />;
  }

  return <Outlet />;
}
