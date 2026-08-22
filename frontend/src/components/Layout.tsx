import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  FolderTree,
  MessageSquare,
  Search,
  GraduationCap,
  Settings,
  Menu,
  X,
  ShieldCheck,
  WifiOff,
} from "lucide-react";
import { useHealth } from "../hooks/queries";
import { t } from "../lib/i18n";

const NAV_ITEMS = [
  { to: "/", label: "nav.dashboard", icon: LayoutDashboard, end: true },
  { to: "/documents", label: "nav.documents", icon: FileText, end: false },
  { to: "/knowledge-bases", label: "nav.knowledgeBases", icon: FolderTree, end: false },
  { to: "/chat", label: "nav.chat", icon: MessageSquare, end: false },
  { to: "/search", label: "nav.search", icon: Search, end: false },
  { to: "/study", label: "nav.study", icon: GraduationCap, end: false },
  { to: "/settings", label: "nav.settings", icon: Settings, end: false },
];

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { data: health } = useHealth(30_000);
  const modelOk = health?.model?.provider && health.model.provider !== "";

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-mv-primary)] text-white">
          <ShieldCheck size={20} />
        </div>
        <div>
          <div className="text-sm font-bold leading-tight">{t("app.name")}</div>
          <div className="text-[10px] text-[var(--color-mv-muted)]">{t("app.tagline")}</div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-2" aria-label="Main navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-[var(--color-mv-primary-soft)] text-[var(--color-mv-primary)]"
                  : "text-[var(--color-mv-muted)] hover:bg-[var(--color-mv-bg)] hover:text-[var(--color-mv-text)]"
              }`
            }
          >
            <Icon size={17} />
            {t(label as never)}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-[var(--color-mv-border)] px-4 py-3 text-[11px] text-[var(--color-mv-muted)]">
        <div className="flex items-center gap-1.5">
          <WifiOff size={13} />
          <span>{t("dashboard.offline")}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-[var(--color-mv-border)] bg-[var(--color-mv-surface)] md:block">
        {sidebar}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 bg-[var(--color-mv-surface)] shadow-xl">
            <button
              className="absolute right-3 top-3 p-1 text-[var(--color-mv-muted)]"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-mv-border)] bg-[var(--color-mv-surface)] px-4">
          <div className="flex items-center gap-3">
            <button
              className="p-1.5 text-[var(--color-mv-muted)] md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-2 text-xs">
              <span className={`h-2 w-2 rounded-full ${modelOk ? "bg-[var(--color-mv-success)]" : "bg-[var(--color-mv-warning)]"}`} />
              <span className="text-[var(--color-mv-muted)]">
                {modelOk ? t("dashboard.modelAvailable") : t("dashboard.modelUnavailable")}
              </span>
              <span className="text-[var(--color-mv-border)]">|</span>
              <span className="flex items-center gap-1 font-medium text-[var(--color-mv-success)]">
                <WifiOff size={13} />
                {t("dashboard.localMode")}
              </span>
            </div>
          </div>
          <div className="text-xs text-[var(--color-mv-muted)] hidden sm:block">
            {location.pathname === "/chat" ? t("chat.model") : ""}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
