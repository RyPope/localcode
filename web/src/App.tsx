import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { api } from "./api";
import Header from "./components/Header";
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
    <Suspense fallback={null}>
      <Workspace key={slug} />
    </Suspense>
  );
}

export default function App() {
  const status = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: (q) => (q.state.data?.imported ? false : 1500),
  });
  if (status.isLoading) return null;
  if (!status.data?.imported) return <Setup />;
  return (
    <div className="app-shell">
      <Header />
      <Routes>
        <Route path="/" element={<ProblemList />} />
        <Route path="/problems/:slug" element={<WorkspaceRoute />} />
        <Route path="/companies" element={<CompanyIndex />} />
        <Route path="/companies/:slug" element={<CompanyPage />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/setup" element={<Setup />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
