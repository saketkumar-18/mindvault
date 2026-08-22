import { Routes, Route, Navigate } from "react-router-dom";
import { useFirstRun } from "./hooks/queries";
import { Spinner } from "./components/ui";
import { ToastProvider } from "./components/Toast";
import Layout from "./components/Layout";
import FirstRun from "./pages/FirstRun";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import KnowledgeBases from "./pages/KnowledgeBases";
import Chat from "./pages/Chat";
import SearchPage from "./pages/SearchPage";
import Study from "./pages/Study";
import Settings from "./pages/Settings";

function AppRoutes() {
  const { data: firstRun, isLoading } = useFirstRun();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  // First-run wizard gates the app until setup is complete.
  if (firstRun && !firstRun.completed) {
    return <FirstRun />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/knowledge-bases" element={<KnowledgeBases />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/study" element={<Study />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppRoutes />
    </ToastProvider>
  );
}
