"use client";

import Link from "next/link";
import { use } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ROUTES } from "@/constants/routes";
import { useOrg } from "@/queries/orgs";

export default function OrgDetailPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = use(params);
  const { data: org, isLoading } = useOrg(orgId);

  if (isLoading) return <p className="p-8 text-muted-foreground">Loading…</p>;
  if (!org) return <p className="p-8 text-destructive">Organization not found.</p>;

  return (
    <div className="mx-auto max-w-4xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{org.name}</h1>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={ROUTES.orgs.members(orgId)}>Members</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href={ROUTES.orgs.settings(orgId)}>Settings</Link>
          </Button>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p>
            <span className="font-medium">Slug:</span> {org.slug}
          </p>
          <p>
            <span className="font-medium">Created:</span>{" "}
            {new Date(org.created_at).toLocaleDateString()}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
