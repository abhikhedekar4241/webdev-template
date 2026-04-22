"use client";

import { useAdminStats } from "@/queries/admin";
import { Users, Building2, HardDrive } from "lucide-react";

export default function AdminDashboard() {
  const { data: stats, isLoading } = useAdminStats();

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 rounded-xl bg-muted" />
        <div className="h-64 rounded-xl bg-muted" />
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const statCards = [
    {
      label: "Total Users",
      value: stats?.user_count,
      icon: Users,
      color: "text-blue-600 bg-blue-100",
    },
    {
      label: "Total Organizations",
      value: stats?.org_count,
      icon: Building2,
      color: "text-purple-600 bg-purple-100",
    },
    {
      label: "Storage Used",
      value: formatBytes(stats?.total_storage_bytes || 0),
      icon: HardDrive,
      color: "text-amber-600 bg-amber-100",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Overview</h2>
        <p className="text-muted-foreground">Global system statistics and metrics.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className={`rounded-lg p-2 ${card.color}`}>
                <card.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{card.label}</p>
                <p className="text-2xl font-bold">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="mb-4 font-semibold">System Status</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">API Backend</span>
            <span className="flex items-center gap-1.5 font-medium text-green-600">
              <span className="h-2 w-2 rounded-full bg-green-600" />
              Operational
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Database</span>
            <span className="flex items-center gap-1.5 font-medium text-green-600">
              <span className="h-2 w-2 rounded-full bg-green-600" />
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
