"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiError } from "@/lib/apiError";
import { apiKeysService } from "@/services/apiKeys";

export function useApiKeys(orgId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
    queryFn: () => apiKeysService.list(orgId),
    enabled: !!orgId,
  });
}

export function useCreateApiKey(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => apiKeysService.create(orgId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
      });
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create API key"));
    },
  });
}

export function useRevokeApiKey(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => apiKeysService.revoke(orgId, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
      });
      toast.success("API key revoked");
    },
    onError: () => {
      toast.error("Failed to revoke API key");
    },
  });
}
