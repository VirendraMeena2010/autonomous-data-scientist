import { Navigate, Route, Routes } from "react-router-dom";

import {
  RequireAuthentication,
  RequireGuest,
} from "@/components/auth/auth-route-guards";
import { AppShell } from "@/components/layout/app-shell";
import Login from "@/pages/auth/Login";
import Signup from "@/pages/auth/Signup";
import AnalysisPage from "@/pages/analyses/AnalysisPage";
import DatasetDetails from "@/pages/datasets/DatasetDetails";
import Projects from "@/pages/projects/Projects";
import ProjectWorkspace from "@/pages/projects/ProjectWorkspace";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<RequireGuest />}>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Route>

      <Route element={<RequireAuthentication />}>
        <Route element={<AppShell />}>
          <Route path="/projects" element={<Projects />} />
          <Route
            path="/projects/:projectId"
            element={<ProjectWorkspace />}
          />
          <Route
            path="/projects/:projectId/datasets/:datasetId"
            element={<DatasetDetails />}
          />
          <Route
            path="/projects/:projectId/analyses/:analysisId"
            element={<AnalysisPage />}
          />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
