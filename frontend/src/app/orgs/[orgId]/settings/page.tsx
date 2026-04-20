"use client";

import { use } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useOrg, useUpdateOrg, useDeleteOrg } from "@/queries/orgs";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9-]+$/, "Slug may only contain lowercase letters, numbers, and hyphens"),
});

type FormData = z.infer<typeof schema>;

export default function OrgSettingsPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = use(params);
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

  if (isLoading) return <p className="p-8 text-muted-foreground">Loading…</p>;
  if (!org) return <p className="p-8 text-destructive">Organization not found.</p>;

  return (
    <div className="mx-auto max-w-md space-y-6 p-8">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>General</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => updateOrg(data))} className="space-y-4">
            <div className="space-y-1">
              <Input placeholder="Organization name" {...register("name")} />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <Input placeholder="slug" {...register("slug")} />
              {errors.slug && (
                <p className="text-sm text-destructive">{errors.slug.message}</p>
              )}
            </div>
            <Button type="submit" disabled={isUpdating}>
              {isUpdating ? "Saving…" : "Save changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger zone</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            disabled={isDeleting}
            onClick={() => {
              if (confirm("Delete this organization? This cannot be undone.")) {
                deleteOrg(orgId);
              }
            }}
          >
            {isDeleting ? "Deleting…" : "Delete organization"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
