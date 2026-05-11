import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, BriefcaseBusiness, Database } from "lucide-react";
import { useState } from "react";

import { getDashboardAuthStatus, getDashboardToken, setDashboardToken } from "./api/client";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { DatabasePage } from "./features/database/DatabasePage";
import { JobsPage } from "./features/jobs/JobsPage";
import "./styles.css";

type View = "jobs" | "analytics" | "database";

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false }
        }
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <DashboardApp />
    </QueryClientProvider>
  );
}

function DashboardApp() {
  const auth = useQuery({
    queryKey: ["dashboard-auth"],
    queryFn: getDashboardAuthStatus,
    staleTime: 60_000
  });
  const [token, setToken] = useState(() => getDashboardToken());

  if (auth.isLoading) {
    return <div className="auth-shell">Loading dashboard</div>;
  }

  if (auth.isError) {
    return <div className="auth-shell">Unable to load dashboard authentication state</div>;
  }

  if (auth.data?.token_required && !token) {
    return (
      <TokenGate
        onSubmit={(nextToken) => {
          setDashboardToken(nextToken);
          setToken(nextToken);
        }}
      />
    );
  }

  return (
    <DashboardShell
      onClearToken={
        auth.data?.token_required
          ? () => {
              setDashboardToken(null);
              setToken(null);
            }
          : undefined
      }
    />
  );
}

function TokenGate({ onSubmit }: { onSubmit: (token: string) => void }) {
  const [value, setValue] = useState("");

  return (
    <main className="auth-shell">
      <form
        className="auth-card"
        onSubmit={(event) => {
          event.preventDefault();
          const token = value.trim();
          if (token) {
            onSubmit(token);
          }
        }}
      >
        <h1>API token required</h1>
        <label className="filter-field">
          <span>API token</span>
          <Input
            aria-label="API token"
            autoComplete="current-password"
            onChange={(event) => setValue(event.target.value)}
            type="password"
            value={value}
          />
        </label>
        <Button disabled={!value.trim()} type="submit" variant="primary">
          Unlock dashboard
        </Button>
      </form>
    </main>
  );
}

function DashboardShell({ onClearToken }: { onClearToken?: () => void }) {
  const [view, setView] = useState<View>("jobs");

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <span className="brand-mark">JS</span>
          <div>
            <h1>Job Search</h1>
            <p>Pipeline Console</p>
          </div>
        </div>

        <nav className="nav">
          <button
            className={view === "jobs" ? "nav-item nav-item--active" : "nav-item"}
            onClick={() => setView("jobs")}
            type="button"
          >
            <BriefcaseBusiness aria-hidden="true" size={18} />
            Jobs
          </button>
          <button
            className={view === "analytics" ? "nav-item nav-item--active" : "nav-item"}
            onClick={() => setView("analytics")}
            type="button"
          >
            <BarChart3 aria-hidden="true" size={18} />
            Analytics
          </button>
          <button
            className={view === "database" ? "nav-item nav-item--active" : "nav-item"}
            onClick={() => setView("database")}
            type="button"
          >
            <Database aria-hidden="true" size={18} />
            Database
          </button>
        </nav>

        {onClearToken ? (
          <Button className="token-reset" onClick={onClearToken} type="button">
            Reset API token
          </Button>
        ) : null}
      </aside>

      <main className="main">
        {view === "jobs" ? <JobsPage /> : null}
        {view === "analytics" ? <AnalyticsPage /> : null}
        {view === "database" ? <DatabasePage /> : null}
      </main>
    </div>
  );
}
