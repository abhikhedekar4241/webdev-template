"use client";

import Link from "next/link";
import {
  Users,
  DollarSign,
  Activity,
  ShoppingCart,
  ArrowUpRight,
  Plus,
  Download,
  RefreshCw,
  MoreHorizontal,
  Mail,
} from "lucide-react";
import { useMe } from "@/queries/auth";
import { useInvitations } from "@/queries/invitations";
import { ROUTES } from "@/constants/routes";
import { StatCard } from "@/components/dashboard/StatCard";
import { BarChart } from "@/components/dashboard/BarChart";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { TeamTable } from "@/components/dashboard/TeamTable";

const actions = [
  { label: "New record", icon: Plus, primary: true },
  { label: "Export data", icon: Download, primary: false },
  { label: "Sync", icon: RefreshCw, primary: false },
];

export default function DashboardPage() {
  const { data: me, isLoading: userLoading } = useMe();
  const { data: invitations } = useInvitations();

  if (userLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const firstName = me?.full_name?.split(" ")[0] ?? "there";
  const pendingInvCount = invitations?.length ?? 0;

  return (
    <div className="px-6 py-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
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

      {/* Pending Invitations Alert */}
      {pendingInvCount > 0 && (
        <div className="flex items-center justify-between rounded-xl border border-primary/20 bg-primary/5 px-6 py-4 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold text-sm">You have {pendingInvCount} pending invitation{pendingInvCount !== 1 ? "s" : ""}</p>
              <p className="text-xs text-muted-foreground font-medium">Join an organization to start collaborating with your team.</p>
            </div>
          </div>
          <Link
            href={ROUTES.orgs.list}
            className="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
          >
            Review Invitations
          </Link>
        </div>
      )}

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

      {/* Team table */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h2 className="font-semibold">Team members</h2>
            <p className="text-xs text-muted-foreground">Manage your organization members</p>
          </div>
          <button className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90">
            <Plus className="h-3.5 w-3.5" />
            Add member
          </button>
        </div>
        <TeamTable />
      </div>
    </div>
  );
}
