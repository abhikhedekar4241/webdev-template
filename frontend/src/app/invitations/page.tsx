"use client";

import { InvitationCard } from "@/components/shared/InvitationCard";
import { useInvitations } from "@/queries/invitations";

export default function InvitationsPage() {
  const { data: invitations, isLoading } = useInvitations();

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Pending Invitations</h1>

      {isLoading && <p className="text-muted-foreground">Loading…</p>}

      {!isLoading && (!invitations || invitations.length === 0) && (
        <p className="text-muted-foreground">No pending invitations.</p>
      )}

      <div className="space-y-4">
        {invitations?.map((inv) => (
          <InvitationCard key={inv.id} invitation={inv} />
        ))}
      </div>
    </div>
  );
}
