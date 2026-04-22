"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  LayoutDashboard,
  BarChart3,
  Users,
  FileText,
  Settings,
  Moon,
  Sun,
  LogOut,
  Bell,
  Building2,
  ChevronDown,
  Mail,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";
import { useLogout, useMe } from "@/queries/auth";
import { useOrg } from "@/hooks/useOrg";
import { useOrgs } from "@/queries/orgs";
import { useNotifications } from "@/queries/notifications";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/users", label: "Users", icon: Users },
  { href: "/documents", label: "Documents", icon: FileText },
];

const bottomItems = [
  { href: ROUTES.orgs.list, label: "Organizations", icon: Building2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const logout = useLogout();
  const { data: me, isLoading } = useMe();
  const { data: orgs } = useOrgs();
  const { data: notifications } = useNotifications();
  const { activeOrg, setActiveOrg } = useOrg();
  const router = useRouter();

  const unreadCount = notifications?.filter((n) => !n.read_at).length || 0;

  // Redirect to onboarding if not completed
  useEffect(() => {
    if (!isLoading && me && !me.onboarding_completed_at && pathname !== "/onboarding") {
      router.push("/onboarding");
    }
  }, [me, isLoading, pathname, router]);

  // Auto-select first org if none is active
  useEffect(() => {
    if (orgs && orgs.length > 0 && !activeOrg) {
      const first = orgs[0];
      setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
    }
  }, [orgs, activeOrg, setActiveOrg]);

  const initials = me?.full_name
    ? me.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?";

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="hidden w-56 shrink-0 flex-col border-r border-border bg-card md:flex overflow-y-auto">
        {/* Logo */}
        <div className="flex h-14 items-center gap-2.5 border-b border-border px-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-sm">
            <LayoutDashboard className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-sm font-semibold">Boilerplate</span>
        </div>

        {/* Org switcher */}
        {orgs && orgs.length > 0 && (
          <div className="border-b border-border px-3 py-2.5">
            <div className="relative">
              <select
                className="w-full appearance-none rounded-md border border-border bg-muted/50 py-1.5 pl-2.5 pr-7 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-ring"
                value={activeOrg?.id ?? ""}
                onChange={(e) => {
                  const org = orgs.find((o) => o.id === e.target.value);
                  if (org) setActiveOrg({ id: org.id, name: org.name, slug: org.slug });
                }}
              >
                <option value="" disabled>Select workspace…</option>
                {orgs.map((org) => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
            </div>
          </div>
        )}

        {/* Main nav */}
        <nav className="flex-1 space-y-0.5 px-3 py-3">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : "font-normal text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Bottom nav */}
        <div className="border-t border-border px-3 py-3 space-y-0.5">
          {bottomItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : "font-normal text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </div>

        {/* User footer */}
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium leading-none">{me?.full_name}</p>
              <p className="truncate text-[11px] text-muted-foreground">{me?.email}</p>
            </div>
            <div className="flex items-center gap-0.5">
              <button
                onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
                className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label="Toggle theme"
              >
                <Sun className="h-3.5 w-3.5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-3.5 w-3.5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              </button>
              <button
                onClick={logout}
                className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label="Log out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-6">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 md:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <LayoutDashboard className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">Boilerplate</span>
          </div>

          {/* Page breadcrumb placeholder — pages can override via portal if needed */}
          <div className="hidden md:block" />

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <Link
              href="/notifications"
              className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Link>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              {initials}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
