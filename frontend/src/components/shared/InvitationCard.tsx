"use client";

import { Building2, Clock, Check, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABELS } from "@/constants/roles";
import { useAcceptInvitation, useDeclineInvitation } from "@/queries/invitations";
import type { InvitationData } from "@/services/invitations";
import type { Role } from "@/constants/roles";

interface InvitationCardProps {
  invitation: InvitationData;
  onSuccess?: () => void;
}

export function InvitationCard({ invitation, onSuccess }: InvitationCardProps) {
  const { mutate: accept, isPending: isAccepting } = useAcceptInvitation();
  const { mutate: decline, isPending: isDeclining } = useDeclineInvitation();
  const isPending = isAccepting || isDeclining;

  const handleAccept = () => {
    accept(invitation.id, {
      onSuccess: () => {
        onSuccess?.();
      },
    });
  };

  const expiresAt = new Date(invitation.expires_at);
  const daysLeft = Math.ceil((expiresAt.getTime() - Date.now()) / 86_400_000);
  const expiringSoon = daysLeft <= 2;

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start gap-4 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
          <Building2 className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold">{invitation.org_name}</p>
            <Badge variant={invitation.role as Role}>
              {ROLE_LABELS[invitation.role as Role]}
            </Badge>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">
            You&apos;ve been invited to join as a{" "}
            <span className="font-medium text-foreground">
              {ROLE_LABELS[invitation.role as Role].toLowerCase()}
            </span>
            .
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <Clock className={`h-3.5 w-3.5 ${expiringSoon ? "text-amber-500" : "text-muted-foreground"}`} />
            <span className={`text-xs ${expiringSoon ? "text-amber-600 font-medium" : "text-muted-foreground"}`}>
              {daysLeft > 0
                ? `Expires in ${daysLeft} day${daysLeft !== 1 ? "s" : ""}`
                : "Expires today"}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2 border-t border-border bg-muted/30 px-5 py-3">
        <button
          disabled={isPending}
          onClick={handleAccept}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
        >
          <Check className="h-3.5 w-3.5" />
          {isAccepting ? "Accepting…" : "Accept"}
        </button>
        <button
          disabled={isPending}
          onClick={() => decline(invitation.id)}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-4 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
        >
          <X className="h-3.5 w-3.5" />
          {isDeclining ? "Declining…" : "Decline"}
        </button>
      </div>
    </div>
  );
}
