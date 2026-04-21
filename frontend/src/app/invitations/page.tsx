"use client";

import { Mail } from "lucide-react";
import { InvitationCard } from "@/components/shared/InvitationCard";
import { useInvitations } from "@/queries/invitations";

export default function InvitationsPage() {
  const { data: invitations, isLoading } = useInvitations();

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Invitations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Organizations that have invited you to join
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      )}

      {!isLoading && (!invitations || invitations.length === 0) && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card py-16 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-muted">
            <Mail className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="text-base font-semibold">No pending invitations</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            When someone invites you to an organization, it will appear here.
          </p>
        </div>
      )}

      <div className="space-y-3">
        {invitations?.map((inv) => (
          <InvitationCard key={inv.id} invitation={inv} />
        ))}
      </div>
    </div>
  );
}
