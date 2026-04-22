"use client";

import Link from "next/link";
import { Users, Settings, Calendar, Hash } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { useOrgBySlug } from "@/queries/orgs";

export default function OrgDetailPage({ params }: { params: { orgSlug: string } }) {
  const { orgSlug } = params;
  const { data: org, isLoading } = useOrgBySlug(orgSlug);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8">
        <div className="h-8 w-48 animate-pulse rounded-lg bg-muted" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8">
        <p className="text-destructive">Organization not found.</p>
      </div>
    );
  }

  const quickLinks = [
    {
      href: ROUTES.orgs.members(org.slug),
      icon: Users,
      label: "Members",
      description: "Manage who has access",
      color: "text-blue-500 bg-blue-50 dark:bg-blue-950/40",
    },
    {
      href: ROUTES.orgs.settings(org.slug),
      icon: Settings,
      label: "Settings",
      description: "Update name, slug, and more",
      color: "text-slate-500 bg-slate-100 dark:bg-slate-800",
    },
  ];

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-violet-600 text-lg font-bold text-white shadow-sm">
          {org.name[0].toUpperCase()}
        </div>
        <h1 className="mt-3 text-2xl font-bold">{org.name}</h1>
        <p className="mt-1 text-sm text-muted-foreground">/{org.slug}</p>
      </div>

      {/* Quick links */}
      <div className="mb-8 grid gap-3 sm:grid-cols-2">
        {quickLinks.map(({ href, icon: Icon, label, description, color }) => (
          <Link
            key={href}
            href={href}
            className="group flex items-center gap-4 rounded-xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold group-hover:text-primary transition-colors">{label}</p>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Details */}
      <div className="rounded-xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-semibold">Details</h2>
        </div>
        <div className="divide-y divide-border">
          <div className="flex items-center gap-3 px-5 py-3.5">
            <Hash className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="w-24 text-sm text-muted-foreground">Slug</span>
            <span className="text-sm font-medium">{org.slug}</span>
          </div>
          <div className="flex items-center gap-3 px-5 py-3.5">
            <Calendar className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="w-24 text-sm text-muted-foreground">Created</span>
            <span className="text-sm font-medium">
              {new Date(org.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
