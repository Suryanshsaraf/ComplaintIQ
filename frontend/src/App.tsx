import { Activity, BellRing, Brain, FileSearch, LayoutDashboard, Menu, MessageSquareText, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Badge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import AlertCenter from "@/pages/AlertCenter";
import Explorer from "@/pages/Explorer";
import MLIntelligence from "@/pages/MLIntelligence";
import NLPIntelligence from "@/pages/NLPIntelligence";
import Overview from "@/pages/Overview";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/explorer", label: "Complaint Explorer", icon: FileSearch },
  { to: "/nlp", label: "NLP Intelligence", icon: MessageSquareText },
  { to: "/ml", label: "ML Intelligence", icon: Brain },
  { to: "/alerts", label: "Alert Center", icon: BellRing },
];

export default function App() {
  const [open, setOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("complaintiq-theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("complaintiq-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("complaintiq-theme", "light");
    }
  }, [darkMode]);

  const alerts = useApi<Record<string, number>>("/api/alerts/counts");
  const health = useApi<{ complaints: number }>("/api/health");
  const activeAlerts = alerts.data ? Object.entries(alerts.data).filter(([k]) => k !== "resolved").reduce((a, [, v]) => a + v, 0) : 0;
  const stats = useApi<any>("/api/datasets/stats");

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 transform border-r bg-card p-4 transition-transform md:static md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="mb-6 flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <p className="text-base font-semibold leading-none">ComplaintIQ</p>
              <p className="text-[11px] text-muted-foreground">Early-warning system</p>
            </div>
          </div>
          <button
            type="button"
            aria-label="Toggle theme"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-input bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {darkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
        <nav className="space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{label}</span>
              {to === "/alerts" && activeAlerts > 0 && <Badge className="border-red-200 bg-red-100 text-red-700">{activeAlerts}</Badge>}
            </NavLink>
          ))}
        </nav>
        <div className="absolute inset-x-4 bottom-4 rounded-md border bg-muted/50 p-3 text-xs text-muted-foreground">
          <p className="font-medium text-foreground">{health.data ? `${health.data.complaints.toLocaleString()} complaints` : "Connecting…"}</p>
          {stats.data?.is_fully_synthetic && <p className="mt-1">Dataset is <b>synthetic</b> (generated for demonstration).</p>}
          {stats.data && !stats.data.is_fully_synthetic && stats.data.synthetic > 0 && <p className="mt-1">Includes {stats.data.synthetic.toLocaleString()} synthetic rows.</p>}
          {health.error && <p className="mt-1 text-red-600">API unreachable</p>}
        </div>
      </aside>
      {open && <div className="fixed inset-0 z-30 bg-black/30 md:hidden" onClick={() => setOpen(false)} />}
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b bg-card px-4 py-3 md:hidden">
          <div className="flex items-center gap-3">
            <button aria-label="Open menu" onClick={() => setOpen(true)}>
              <Menu className="h-5 w-5" />
            </button>
            <span className="font-semibold">ComplaintIQ</span>
          </div>
          <button
            type="button"
            aria-label="Toggle theme"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-input bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {darkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </button>
        </header>
        <main className="mx-auto max-w-[1400px] p-4 md:p-8">
          <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/explorer" element={<Explorer />} />
            <Route path="/nlp" element={<NLPIntelligence />} />
            <Route path="/ml" element={<MLIntelligence />} />
            <Route path="/alerts" element={<AlertCenter />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
