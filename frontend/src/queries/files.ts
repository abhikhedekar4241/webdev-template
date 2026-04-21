"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { filesService } from "@/services/files";

export function useUploadFile(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => filesService.upload(orgId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.files.list(orgId) });
      toast.success("File uploaded");
    },
    onError: () => {
      toast.error("Failed to upload file");
    },
  });
}

export function useGetFileUrl() {
  return useMutation({
    mutationFn: (fileId: string) => filesService.getUrl(fileId),
    onError: () => {
      toast.error("Failed to get file URL");
    },
  });
}

export function useDeleteFile(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (fileId: string) => filesService.delete(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.files.list(orgId) });
      toast.success("File deleted");
    },
    onError: () => {
      toast.error("Failed to delete file");
    },
  });
}
