import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import Header from "./components/Header";
import { useAppStatus } from "./hooks/useAppStatus";
import CompanyIndex from "./pages/CompanyIndex";
import CompanyPage from "./pages/CompanyPage";
import ProblemList from "./pages/ProblemList";
import Progress from "./pages/Progress";
import Setup from "./pages/Setup";

// The workspace pulls in Monaco (~4 MB); load it only when a problem is opened.
const Workspace = lazy(() => import("./pages/Workspace"));

/** One Workspace instance per problem, so editor state can never carry over between problems. */
function WorkspaceRoute() {
  const { slug = "" } = useParams();
  return (
    <Suspense fallback={<div className="empty">Loading editor…</div>}>
      <Workspace key={slug} />
    </Suspense>
  );
}

export default function App() {
  const status = useAppStatus();
  const location = useLocation();

  if (status.isPending) return null;
  if (status.isError) {
    return (
      <main className="page" role="alert">
        <h1 className="title-1">Can't reach the localcode server</h1>
        <p className="note text-sm">{status.error.message}. Is the app container running (`docker compose up -d`)?</p>
      </main>
    );
  }
  if (!status.data.imported) return <Setup />;
  return (
    <div className="app-shell">
      <Header />
      <ErrorBoundary key={location.pathname}>
        <Routes>
          <Route path="/" element={<ProblemList />} />
          <Route path="/problems/:slug" element={<WorkspaceRoute />} />
          <Route path="/companies" element={<CompanyIndex />} />
          <Route path="/companies/:slug" element={<CompanyPage />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ErrorBoundary>
    </div>
  );
}
