"use client";

import Link from "next/link";
import { ArrowLeft, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useOrg, useUpdateOrg, useDeleteOrg } from "@/queries/orgs";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9-]+$/, "Only lowercase letters, numbers, and hyphens"),
});

type FormData = z.infer<typeof schema>;

export default function OrgSettingsPage({ params }: { params: { orgId: string } }) {
  const { orgId } = params;
  const { data: org, isLoading } = useOrg(orgId);
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

  if (isLoading) {
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
        href={`/orgs/${orgId}`}
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
