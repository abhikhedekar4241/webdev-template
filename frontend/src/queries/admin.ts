import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminService } from "@/services/admin";
import { setToken } from "@/services/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => adminService.getStats(),
  });
}

export function useAdminUsers(params: {
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  search?: string;
}) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: () => adminService.listUsers(params),
  });
}

export function useAdminOrgs(params: {
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  search?: string;
}) {
  return useQuery({
    queryKey: ["admin", "orgs", params],
    queryFn: () => adminService.listOrgs(params),
  });
}

export function useImpersonate() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => adminService.impersonate(userId),
    onSuccess: (data) => {
      setToken(data.access_token);
      queryClient.clear();
      toast.success("Impersonation active");
      router.push("/dashboard");
    },
    onError: () => {
      toast.error("Failed to impersonate user");
    },
  });
}
