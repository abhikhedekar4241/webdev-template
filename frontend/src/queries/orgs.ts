"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { ROUTES } from "@/constants/routes";
import { getApiError } from "@/lib/apiError";
import { orgsService } from "@/services/orgs";
import { useOrgStore } from "@/store/org";

export function useOrgs() {
  return useQuery({
    queryKey: QUERY_KEYS.orgs.list,
    queryFn: orgsService.list,
  });
}

export function useOrg(orgId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.orgs.detail(orgId),
    queryFn: () => orgsService.get(orgId),
    enabled: !!orgId,
  });
}

export function useOrgBySlug(slug: string) {
  return useQuery({
    queryKey: ["orgs", "slug", slug],
    queryFn: () => orgsService.getBySlug(slug),
    enabled: !!slug,
  });
}

export function useCreateOrg() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  return useMutation({
    mutationFn: (data: { name: string; slug: string }) =>
      orgsService.create(data),
    onSuccess: (org) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orgs.list });
      setActiveOrg({ id: org.id, name: org.name, slug: org.slug });
      toast.success("Organization created");
      router.push(ROUTES.orgs.detail(org.slug));
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create organization"));
    },
  });
}

export function useUpdateOrg(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name?: string; slug?: string }) =>
      orgsService.update(orgId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.detail(orgId),
      });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orgs.list });
      toast.success("Organization updated");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to update organization"));
    },
  });
}

export function useDeleteOrg() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  return useMutation({
    mutationFn: (orgId: string) => orgsService.delete(orgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orgs.list });
      setActiveOrg(null);
      toast.success("Organization deleted");
      router.push(ROUTES.orgs.list);
    },
    onError: () => {
      toast.error("Failed to delete organization");
    },
  });
}

export function useOrgMembers(orgId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.orgs.members(orgId),
    queryFn: () => orgsService.listMembers(orgId),
    enabled: !!orgId,
  });
}

export function useChangeMemberRole(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      orgsService.changeMemberRole(orgId, userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.members(orgId),
      });
      toast.success("Role updated");
    },
    onError: () => {
      toast.error("Failed to update role");
    },
  });
}

export function useRemoveMember(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => orgsService.removeMember(orgId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.members(orgId),
      });
      toast.success("Member removed");
    },
    onError: () => {
      toast.error("Failed to remove member");
    },
  });
}
