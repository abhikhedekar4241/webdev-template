"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ROUTES } from "@/constants/routes";
import { useOrgs } from "@/queries/orgs";

export default function OrgsPage() {
  const { data: orgs, isLoading } = useOrgs();

  return (
    <div className="mx-auto max-w-4xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Organizations</h1>
        <Button asChild>
          <Link href={ROUTES.orgs.new}>New organization</Link>
        </Button>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading…</p>}

      {!isLoading && orgs?.length === 0 && (
        <p className="text-muted-foreground">
          You are not a member of any organizations yet.
        </p>
      )}

      <div className="space-y-3">
        {orgs?.map((org) => (
          <Card key={org.id}>
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{org.name}</CardTitle>
                <Button variant="outline" size="sm" asChild>
                  <Link href={ROUTES.orgs.detail(org.id)}>Open</Link>
                </Button>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
