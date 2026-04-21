"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateOrg } from "@/queries/orgs";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9-]+$/, "Only lowercase letters, numbers, and hyphens"),
});

type FormData = z.infer<typeof schema>;

export default function NewOrgPage() {
  const { mutate: createOrg, isPending } = useCreateOrg();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const slug = watch("slug") ?? "";

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const auto = e.target.value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    if (auto) {
      setValue("slug", auto, { shouldValidate: true });
    }
  };

  return (
    <div className="mx-auto max-w-lg px-6 py-8">
      <Link
        href="/orgs"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to organizations
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">New organization</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Create a workspace to collaborate with your team.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <form onSubmit={handleSubmit((data) => createOrg(data))} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Organization name</label>
            <input
              placeholder="Acme Inc."
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              {...register("name")}
              onChange={(e) => {
                register("name").onChange(e);
                handleNameChange(e);
              }}
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">URL slug</label>
            <div className="flex items-center gap-0 overflow-hidden rounded-lg border border-input bg-background focus-within:ring-2 focus-within:ring-ring">
              <span className="select-none border-r border-input bg-muted px-3 py-2 text-sm text-muted-foreground">
                app/
              </span>
              <input
                placeholder="acme-inc"
                className="flex-1 bg-transparent px-3 py-2 text-sm focus:outline-none"
                {...register("slug")}
              />
            </div>
            {errors.slug ? (
              <p className="text-xs text-destructive">{errors.slug.message}</p>
            ) : slug ? (
              <p className="text-xs text-muted-foreground">
                Your workspace will be at <span className="font-medium">app/{slug}</span>
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isPending || !slug}
            className="flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {isPending ? "Creating…" : "Create organization"}
          </button>
        </form>
      </div>
    </div>
  );
}
