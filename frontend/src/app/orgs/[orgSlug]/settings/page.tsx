"use client";

import Link from "next/link";
import { ArrowLeft, Trash2, Key, Copy, Check } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useOrgBySlug, useUpdateOrg, useDeleteOrg } from "@/queries/orgs";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/queries/apiKeys";
import type { ApiKeyCreated } from "@/services/apiKeys";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9-]+$/, "Only lowercase letters, numbers, and hyphens"),
});

type FormData = z.infer<typeof schema>;

function ApiKeysSection({ orgId }: { orgId: string }) {
  const { data: keys = [], isLoading } = useApiKeys(orgId);
  const createKey = useCreateApiKey(orgId);
  const revokeKey = useRevokeApiKey(orgId);

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      setCreatedKey(null);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
    };
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const result = await createKey.mutateAsync(newKeyName.trim());
      setCreatedKey(result);
      setNewKeyName("");
    } catch {
      // error handled in mutation
    }
  }

  async function handleCopy() {
    if (!createdKey) return;
    try {
      await navigator.clipboard.writeText(createdKey.key);
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
      setCopied(true);
      copyTimerRef.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for non-HTTPS or unsupported browsers
      try {
        const textarea = document.createElement("textarea");
        textarea.value = createdKey.key;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
        setCopied(true);
        copyTimerRef.current = setTimeout(() => setCopied(false), 2000);
      } catch {
        toast.error("Failed to copy key — please copy it manually.");
      }
    }
  }

  function handleDismiss() {
    if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
    setCreatedKey(null);
    setCopied(false);
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-5 py-4">
        <h2 className="font-semibold">API Keys</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Keys authenticate as the key creator with full org access.
        </p>
      </div>
      <div className="p-5 space-y-4">
        {/* Create form */}
        {!createdKey && (
          <form onSubmit={handleCreate} className="flex gap-2">
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g. CI/CD)"
              className="flex h-9 flex-1 rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <button
              type="submit"
              disabled={createKey.isPending || !newKeyName.trim()}
              className="flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              <Key className="h-3.5 w-3.5" />
              {createKey.isPending ? "Creating…" : "Create"}
            </button>
          </form>
        )}

        {/* Show newly created key — one time only */}
        {createdKey && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Copy your key now — it won&apos;t be shown again.
            </p>
            <div className="flex gap-2">
              <input
                readOnly
                value={createdKey.key}
                className="flex h-9 flex-1 rounded-lg border border-input bg-background px-3 font-mono text-xs focus-visible:outline-none"
              />
              <button
                onClick={handleCopy}
                className="flex h-9 items-center gap-1.5 rounded-lg border border-input bg-background px-3 text-sm hover:bg-muted"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-green-600" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <button
              onClick={handleDismiss}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Done — dismiss
            </button>
          </div>
        )}

        {/* Key list */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : keys.length === 0 ? (
          <p className="text-sm text-muted-foreground">No API keys yet.</p>
        ) : (
          <div className="divide-y divide-border rounded-lg border border-border">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium">{key.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                    {key.key_prefix}…
                    {key.last_used_at
                      ? ` · last used ${new Date(key.last_used_at).toLocaleDateString()}`
                      : " · never used"}
                  </p>
                </div>
                <button
                  onClick={() => {
                    if (confirm(`Revoke "${key.name}"? This cannot be undone.`)) {
                      revokeKey.mutate(key.id);
                    }
                  }}
                  className="rounded-md px-2.5 py-1 text-xs font-medium text-destructive hover:bg-destructive/10"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function OrgSettingsPage({ params }: { params: { orgSlug: string } }) {
  const { orgSlug } = params;
  const { data: org, isLoading: orgLoading } = useOrgBySlug(orgSlug);

  const orgId = org?.id || "";
  const { mutate: updateOrg, isPending: isUpdating } = useUpdateOrg(orgId);
  const { mutate: deleteOrg, isPending: isDeleting } = useDeleteOrg();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: org ? { name: org.name, slug: org.slug } : undefined,
  });

  if (orgLoading) {
    return (
      <div className="mx-auto max-w-lg px-6 py-8">
        <div className="space-y-4">
          <div className="h-6 w-32 animate-pulse rounded bg-muted" />
          <div className="h-48 animate-pulse rounded-xl bg-muted" />
        </div>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="mx-auto max-w-lg px-6 py-8">
        <p className="text-destructive">Organization not found.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-6 py-8 space-y-6">
      <Link
        href={`/orgs/${orgSlug}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to organization
      </Link>

      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your organization details</p>
      </div>

      {/* General settings */}
      <div className="rounded-xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-semibold">General</h2>
        </div>
        <div className="p-5">
          <form onSubmit={handleSubmit((data) => updateOrg(data))} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Organization name</label>
              <input
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">URL slug</label>
              <input
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring font-mono"
                {...register("slug")}
              />
              {errors.slug && (
                <p className="text-xs text-destructive">{errors.slug.message}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={isUpdating}
              className="h-9 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {isUpdating ? "Saving…" : "Save changes"}
            </button>
          </form>
        </div>
      </div>

      <ApiKeysSection orgId={orgId} />

      {/* Danger zone */}
      <div className="rounded-xl border border-destructive/30 bg-card shadow-sm">
        <div className="border-b border-destructive/30 px-5 py-4">
          <h2 className="font-semibold text-destructive">Danger zone</h2>
        </div>
        <div className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium">Delete this organization</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Permanently delete this org and all its data. This cannot be undone.
              </p>
            </div>
            <button
              disabled={isDeleting}
              onClick={() => {
                if (confirm(`Delete "${org.name}"? This cannot be undone.`)) {
                  deleteOrg(orgId);
                }
              }}
              className="flex shrink-0 items-center gap-1.5 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              {isDeleting ? "Deleting…" : "Delete"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
