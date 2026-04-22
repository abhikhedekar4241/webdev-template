"use client";

import Link from "next/link";
import { Plus, Building2, ChevronRight, Mail } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { useOrgs } from "@/queries/orgs";
import { useInvitations } from "@/queries/invitations";
import { InvitationCard } from "@/components/shared/InvitationCard";

function OrgAvatar({ name }: { name: string }) {
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const colors = [
    "from-violet-500 to-indigo-500",
    "from-blue-500 to-cyan-500",
    "from-emerald-500 to-teal-500",
    "from-orange-500 to-amber-500",
    "from-pink-500 to-rose-500",
  ];
  const color = colors[name.charCodeAt(0) % colors.length];

  return (
    <div
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${color} text-sm font-bold text-white shadow-sm`}
    >
      {initials}
    </div>
  );
}

export default function OrgsPage() {
  const { data: orgs, isLoading: orgsLoading } = useOrgs();
  const { data: invitations, isLoading: invsLoading } = useInvitations();

  const isLoading = orgsLoading || invsLoading;

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Organizations</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your workspaces and teams
          </p>
        </div>
        <Link
          href={ROUTES.orgs.new}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          New organization
        </Link>
      </div>

      {/* Pending Invitations */}
      {!isLoading && invitations && invitations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-primary">
            <Mail className="h-4 w-4" />
            <h2 className="text-sm font-bold uppercase tracking-wider">Pending Invitations</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {invitations.map((inv) => (
              <InvitationCard key={inv.id} invitation={inv} />
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && (!orgs || orgs.length === 0) && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card py-16 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-muted">
            <Building2 className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="text-base font-semibold">No organizations yet</h3>
          <p className="mt-1 max-w-xs text-sm text-muted-foreground">
            Create your first organization to invite your team and start collaborating.
          </p>
          <Link
            href={ROUTES.orgs.new}
            className="mt-5 flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            Create organization
          </Link>
        </div>
      )}

      {/* Org list */}
      {!isLoading && orgs && orgs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Building2 className="h-4 w-4" />
            <h2 className="text-sm font-bold uppercase tracking-wider">Your Workspaces</h2>
          </div>
          <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            {orgs.map((org, i) => (
              <Link
                key={org.id}
                href={ROUTES.orgs.detail(org.slug)}
                className={`flex items-center gap-4 px-5 py-4 transition-colors hover:bg-muted/50 ${
                  i > 0 ? "border-t border-border" : ""
                }`}
              >
                <OrgAvatar name={org.name} />
                <div className="flex-1 min-w-0">
                  <p className="truncate font-semibold">{org.name}</p>
                  <p className="truncate text-sm text-muted-foreground">/{org.slug}</p>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
