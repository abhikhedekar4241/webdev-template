"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";
import { useOrgs } from "@/queries/orgs";
import { useOrg } from "@/hooks/useOrg";

export function OrgSwitcher() {
  const { data: orgs } = useOrgs();
  const { activeOrg, setActiveOrg } = useOrg();

  if (!orgs || orgs.length === 0) {
    return (
      <Button variant="outline" size="sm" asChild>
        <Link href={ROUTES.orgs.new}>New org</Link>
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <select
        className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
        value={activeOrg?.id ?? ""}
        onChange={(e) => {
          const org = orgs.find((o) => o.id === e.target.value);
          if (org) setActiveOrg({ id: org.id, name: org.name, slug: org.slug });
        }}
      >
        <option value="" disabled>
          Select org…
        </option>
        {orgs.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}
          </option>
        ))}
      </select>
      {activeOrg && (
        <Button variant="ghost" size="sm" asChild>
          <Link href={ROUTES.orgs.detail(activeOrg.id)}>Open</Link>
        </Button>
      )}
    </div>
  );
}
