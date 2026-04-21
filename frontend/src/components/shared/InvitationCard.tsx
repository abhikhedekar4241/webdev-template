"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { ROLE_LABELS } from "@/constants/roles";
import { useAcceptInvitation, useDeclineInvitation } from "@/queries/invitations";
import type { InvitationData } from "@/services/invitations";

interface InvitationCardProps {
  invitation: InvitationData;
}

export function InvitationCard({ invitation }: InvitationCardProps) {
  const { mutate: accept, isPending: isAccepting } = useAcceptInvitation();
  const { mutate: decline, isPending: isDeclining } = useDeclineInvitation();

  const isPending = isAccepting || isDeclining;

  return (
    <Card>
      <CardContent className="pt-4">
        <p className="font-medium">Organization invitation</p>
        <p className="text-sm text-muted-foreground mt-1">
          You have been invited as a{" "}
          <span className="font-medium">{ROLE_LABELS[invitation.role]}</span>.
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Expires {new Date(invitation.expires_at).toLocaleDateString()}
        </p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button
          size="sm"
          disabled={isPending}
          onClick={() => accept(invitation.id)}
        >
          {isAccepting ? "Accepting…" : "Accept"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={isPending}
          onClick={() => decline(invitation.id)}
        >
          {isDeclining ? "Declining…" : "Decline"}
        </Button>
      </CardFooter>
    </Card>
  );
}
