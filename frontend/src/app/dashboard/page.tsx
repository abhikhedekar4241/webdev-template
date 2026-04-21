"use client";

import {
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  Activity,
  ShoppingCart,
  ArrowUpRight,
  Plus,
  Download,
  RefreshCw,
  MoreHorizontal,
  CheckCircle2,
  Clock,
  AlertCircle,
  Circle,
} from "lucide-react";
import { useMe } from "@/queries/auth";
import { Badge } from "@/components/ui/badge";

// --- Stat card ---

interface StatCardProps {
  label: string;
  value: string;
  change: string;
  up: boolean;
  icon: React.ElementType;
  color: string;
}

function StatCard({ label, value, change, up, icon: Icon, color }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <span
          className={`flex items-center gap-1 text-xs font-medium ${
            up ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"
          }`}
        >
          {up ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
          {change}
        </span>
      </div>
      <p className="mt-4 text-2xl font-bold">{value}</p>
      <p className="mt-0.5 text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

// --- Bar chart (pure CSS) ---

const chartData = [
  { month: "Jan", value: 40 },
  { month: "Feb", value: 62 },
  { month: "Mar", value: 55 },
  { month: "Apr", value: 78 },
  { month: "May", value: 90 },
  { month: "Jun", value: 72 },
  { month: "Jul", value: 85 },
  { month: "Aug", value: 95 },
  { month: "Sep", value: 68 },
  { month: "Oct", value: 80 },
  { month: "Nov", value: 74 },
  { month: "Dec", value: 88 },
];

function BarChart() {
  const max = Math.max(...chartData.map((d) => d.value));
  return (
    <div className="flex h-40 items-end gap-1.5">
      {chartData.map((d) => (
        <div key={d.month} className="group flex flex-1 flex-col items-center gap-1">
          <div
            className="relative w-full rounded-t-md bg-primary/20 transition-all group-hover:bg-primary/40"
            style={{ height: `${(d.value / max) * 100}%` }}
          >
            <div
              className="absolute inset-x-0 bottom-0 rounded-t-md bg-primary transition-all"
              style={{ height: "60%" }}
            />
            {/* Tooltip */}
            <span className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-foreground px-1.5 py-0.5 text-[10px] font-medium text-background opacity-0 group-hover:opacity-100 transition-opacity">
              {d.value}
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground">{d.month}</span>
        </div>
      ))}
    </div>
  );
}

// --- Activity feed ---

const STATUS_ICON = {
  done: { icon: CheckCircle2, className: "text-emerald-500" },
  pending: { icon: Clock, className: "text-amber-500" },
  error: { icon: AlertCircle, className: "text-red-500" },
  info: { icon: Circle, className: "text-blue-500" },
} as const;

type ActivityStatus = keyof typeof STATUS_ICON;

interface ActivityItem {
  id: number;
  title: string;
  subtitle: string;
  time: string;
  status: ActivityStatus;
  badge?: string;
}

const activity: ActivityItem[] = [
  { id: 1, title: "New user registered", subtitle: "alice@example.com joined via invite", time: "2 min ago", status: "done", badge: "User" },
  { id: 2, title: "Payment processed", subtitle: "Invoice #1042 — $249.00", time: "14 min ago", status: "done", badge: "Billing" },
  { id: 3, title: "Background job failed", subtitle: "cleanup_expired_invitations — timeout", time: "32 min ago", status: "error", badge: "Worker" },
  { id: 4, title: "Export requested", subtitle: "users_export.csv — generating", time: "1 hr ago", status: "pending", badge: "Export" },
  { id: 5, title: "Org settings updated", subtitle: "demo-org slug changed by Admin User", time: "2 hr ago", status: "info", badge: "Org" },
  { id: 6, title: "File uploaded", subtitle: "report_q4.pdf (2.4 MB)", time: "3 hr ago", status: "done", badge: "Files" },
];

function ActivityFeed() {
  return (
    <div className="divide-y divide-border">
      {activity.map((item) => {
        const { icon: Icon, className } = STATUS_ICON[item.status];
        return (
          <div key={item.id} className="flex items-start gap-3 px-5 py-3.5">
            <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${className}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium truncate">{item.title}</p>
                {item.badge && (
                  <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                    {item.badge}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground truncate">{item.subtitle}</p>
            </div>
            <span className="shrink-0 text-[11px] text-muted-foreground">{item.time}</span>
          </div>
        );
      })}
    </div>
  );
}

// --- Quick actions ---

const actions = [
  { label: "New record", icon: Plus, primary: true },
  { label: "Export data", icon: Download, primary: false },
  { label: "Sync", icon: RefreshCw, primary: false },
];

// --- Users table ---

const tableUsers = [
  { name: "Alice Martin", email: "alice@example.com", role: "Admin", status: "Active", joined: "Apr 12, 2026" },
  { name: "Bob Chen", email: "bob@example.com", role: "Member", status: "Active", joined: "Apr 14, 2026" },
  { name: "Carol Davis", email: "carol@example.com", role: "Member", status: "Invited", joined: "Apr 18, 2026" },
  { name: "Dan Kim", email: "dan@example.com", role: "Admin", status: "Active", joined: "Mar 30, 2026" },
  { name: "Eve Santos", email: "eve@example.com", role: "Member", status: "Inactive", joined: "Mar 10, 2026" },
];

const STATUS_BADGE: Record<string, string> = {
  Active: "success",
  Invited: "warning",
  Inactive: "secondary",
};

// --- Page ---

export default function DashboardPage() {
  const { data: me } = useMe();
  const firstName = me?.full_name?.split(" ")[0] ?? "there";

  return (
    <div className="px-6 py-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Good morning, {firstName} 👋</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here&apos;s what&apos;s happening with your app today.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {actions.map(({ label, icon: Icon, primary }) => (
            <button
              key={label}
              className={`flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-opacity hover:opacity-80 ${
                primary
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "border border-border bg-card text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total users" value="2,847" change="12% vs last month" up icon={Users} color="bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400" />
        <StatCard label="Monthly revenue" value="$48,295" change="8.1% vs last month" up icon={DollarSign} color="bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400" />
        <StatCard label="Active sessions" value="1,234" change="3.2% vs yesterday" up={false} icon={Activity} color="bg-violet-50 text-violet-600 dark:bg-violet-950/50 dark:text-violet-400" />
        <StatCard label="New orders" value="384" change="5.4% vs last week" up icon={ShoppingCart} color="bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400" />
      </div>

      {/* Chart + Activity */}
      <div className="grid gap-4 lg:grid-cols-5">
        {/* Chart */}
        <div className="lg:col-span-3 rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div>
              <h2 className="font-semibold">Revenue overview</h2>
              <p className="text-xs text-muted-foreground">Monthly revenue for 2026</p>
            </div>
            <button className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted transition-colors">
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </div>
          <div className="px-5 py-5">
            <BarChart />
          </div>
        </div>

        {/* Activity feed */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div>
              <h2 className="font-semibold">Recent activity</h2>
              <p className="text-xs text-muted-foreground">Last 24 hours</p>
            </div>
            <button className="flex items-center gap-1 text-xs font-medium text-primary hover:underline">
              View all <ArrowUpRight className="h-3 w-3" />
            </button>
          </div>
          <ActivityFeed />
        </div>
      </div>

      {/* Users table */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h2 className="font-semibold">Team members</h2>
            <p className="text-xs text-muted-foreground">{tableUsers.length} people in this workspace</p>
          </div>
          <button className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90">
            <Plus className="h-3.5 w-3.5" />
            Add member
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Name</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Role</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Joined</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {tableUsers.map((u, i) => (
                <tr
                  key={u.email}
                  className={`${i > 0 ? "border-t border-border" : ""} hover:bg-muted/30 transition-colors`}
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                        {u.name.split(" ").map((n) => n[0]).join("")}
                      </div>
                      <div>
                        <p className="font-medium">{u.name}</p>
                        <p className="text-xs text-muted-foreground">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <Badge variant={u.role === "Admin" ? "admin" : "member"}>{u.role}</Badge>
                  </td>
                  <td className="px-5 py-3.5">
                    <Badge variant={STATUS_BADGE[u.status] as "success" | "warning" | "secondary"}>
                      {u.status}
                    </Badge>
                  </td>
                  <td className="px-5 py-3.5 text-sm text-muted-foreground">{u.joined}</td>
                  <td className="px-5 py-3.5">
                    <button className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted transition-colors">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
