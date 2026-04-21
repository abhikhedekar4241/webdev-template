"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { invitationsService } from "@/services/invitations";

export function useInvitations() {
  return useQuery({
    queryKey: QUERY_KEYS.invitations.list,
    queryFn: invitationsService.list,
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invId: string) => invitationsService.accept(invId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orgs.list });
      toast.success("Invitation accepted! You are now a member.");
    },
    onError: () => {
      toast.error("Failed to accept invitation");
    },
  });
}

export function useDeclineInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invId: string) => invitationsService.decline(invId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      toast.success("Invitation declined");
    },
    onError: () => {
      toast.error("Failed to decline invitation");
    },
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { org_id: string; email: string; role: string }) =>
      invitationsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      toast.success("Invitation sent");
    },
    onError: () => {
      toast.error("Failed to send invitation");
    },
  });
}
