"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, UserMinus, ShieldCheck, User, UserPlus, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABELS } from "@/constants/roles";
import { useOrgBySlug, useOrgMembers, useRemoveMember, useChangeMemberRole } from "@/queries/orgs";
import { useCreateInvitation } from "@/queries/invitations";
import { useAuth } from "@/hooks/useAuth";
import type { Role } from "@/constants/roles";

function RoleBadge({ role }: { role: Role }) {
  const variantMap: Record<Role, "owner" | "admin" | "member"> = {
    owner: "owner",
    admin: "admin",
    member: "member",
  };
  return <Badge variant={variantMap[role]}>{ROLE_LABELS[role]}</Badge>;
}

function MemberAvatar({ name }: { name: string }) {
  const initials =
    name
      .split(" ")
      .map((w) => w[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "?";
  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
      {initials}
    </div>
  );
}

function InviteForm({ orgId }: { orgId: string }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const { mutate: invite, isPending } = useCreateInvitation();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    invite(
      { org_id: orgId, email, role },
      {
        onSuccess: () => setEmail(""),
      }
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <UserPlus className="h-4 w-4 text-primary" />
          <h2 className="font-semibold">Invite a member</h2>
        </div>
        <p className="mt-0.5 text-sm text-muted-foreground">
          They&apos;ll receive an email invitation to join this organization.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="flex items-end gap-3 p-5">
        <div className="flex-1 space-y-1.5">
          <label className="text-sm font-medium">Email address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="colleague@example.com"
            className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Role</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as "member" | "admin")}
            className="flex h-10 rounded-lg border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={isPending || !email}
          className="flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
        >
          <Send className="h-3.5 w-3.5" />
          {isPending ? "Sending…" : "Send invite"}
        </button>
      </form>
    </div>
  );
}

export default function OrgMembersPage({ params }: { params: { orgSlug: string } }) {
  const { orgSlug } = params;
  const { data: org, isLoading: orgLoading } = useOrgBySlug(orgSlug);
  
  const orgId = org?.id || "";
  const { data: members, isLoading: membersLoading } = useOrgMembers(orgId);
  const { mutate: removeMember, isPending: isRemoving } = useRemoveMember(orgId);
  const { mutate: changeRole, isPending: isChanging } = useChangeMemberRole(orgId);
  const { user } = useAuth();
  const myMembership = members?.find((m) => m.user_id === user?.id);
  const canManage = myMembership?.role === "owner" || myMembership?.role === "admin";

  const isLoading = orgLoading || (!!orgId && membersLoading);

  if (!orgLoading && !org) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8">
        <p className="text-destructive">Organization not found.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-6">
      <Link
        href={`/orgs/${orgSlug}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to organization
      </Link>

      <div>
        <h1 className="text-2xl font-bold">Members</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {members?.length ?? "…"} member{members?.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Invite form */}
      {orgId && canManage && <InviteForm orgId={orgId} />}

      {/* Member list */}
      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      )}

      {!isLoading && members && (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border px-5 py-4">
            <h2 className="font-semibold">Current members</h2>
          </div>
          {members.map((m, i) => {
            const isTargetMe = m.user_id === user?.id;
            const isTargetOwner = m.role === "owner";
            return (
              <div
                key={m.user_id}
                className={`flex items-center gap-4 px-5 py-3.5 ${i > 0 ? "border-t border-border" : ""}`}
              >
                <MemberAvatar name={m.full_name} />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium">
                    {m.full_name}
                    {isTargetMe && (
                      <span className="ml-1.5 text-xs text-muted-foreground">(you)</span>
                    )}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="truncate text-xs text-muted-foreground">{m.email}</p>
                    <RoleBadge role={m.role as Role} />
                  </div>
                </div>
                {canManage && !isTargetMe && !isTargetOwner && (
                  <div className="flex items-center gap-1.5">
                    <button
                      disabled={isChanging}
                      onClick={() =>
                        changeRole({
                          userId: m.user_id,
                          role: m.role === "member" ? "admin" : "member",
                        })
                      }
                      className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground shadow-sm transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
                    >
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {m.role === "member" ? "Make admin" : "Make member"}
                    </button>
                    <button
                      disabled={isRemoving}
                      onClick={() => removeMember(m.user_id)}
                      className="flex items-center gap-1.5 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-1.5 text-xs font-medium text-destructive shadow-sm transition-colors hover:bg-destructive/10 disabled:opacity-50"
                    >
                      <UserMinus className="h-3.5 w-3.5" />
                      Remove
                    </button>
                  </div>
                )}
                {isTargetOwner && !isTargetMe && (
                  <User className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
