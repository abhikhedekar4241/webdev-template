"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { setToken } from "@/services/api";
import { orgsService } from "@/services/orgs";
import { useOrgStore } from "@/store/org";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error || !token) {
      router.push("/auth/login?error=oauth_failed");
      return;
    }

    setToken(token);

    orgsService
      .list()
      .then((orgs) => {
        if (orgs.length > 0) {
          const first = orgs[0];
          setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
        }
      })
      .catch(() => {
        // best-effort org auto-select
      })
      .finally(() => {
        router.push("/dashboard");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <p className="text-sm text-muted-foreground">Signing you in…</p>
    </div>
  );
}
