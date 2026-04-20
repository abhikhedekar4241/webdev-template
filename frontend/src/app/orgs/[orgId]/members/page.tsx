"use client";

import { use } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ROLE_LABELS } from "@/constants/roles";
import { useOrgMembers, useRemoveMember, useChangeMemberRole } from "@/queries/orgs";
import { useAuth } from "@/hooks/useAuth";

export default function OrgMembersPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = use(params);
  const { data: members, isLoading } = useOrgMembers(orgId);
  const { mutate: removeMember } = useRemoveMember(orgId);
  const { mutate: changeRole } = useChangeMemberRole(orgId);
  const { user } = useAuth();

  if (isLoading) return <p className="p-8 text-muted-foreground">Loading…</p>;

  return (
    <div className="mx-auto max-w-4xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Members</h1>
      <div className="space-y-3">
        {members?.map((m) => (
          <Card key={m.user_id}>
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{m.user_id}</p>
                <p className="text-sm text-muted-foreground">{ROLE_LABELS[m.role]}</p>
              </div>
              {m.user_id !== user?.id && (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      changeRole({
                        userId: m.user_id,
                        role: m.role === "member" ? "admin" : "member",
                      })
                    }
                  >
                    Toggle role
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeMember(m.user_id)}
                  >
                    Remove
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
