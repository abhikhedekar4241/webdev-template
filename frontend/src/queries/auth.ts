import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth";
import { orgsService } from "@/services/orgs";
import { useOrgStore } from "@/store/org";
import { useRouter } from "next/navigation";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => authService.me(),
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const { activeOrg, setActiveOrg } = useOrgStore();
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      if (!activeOrg) {
        try {
          const orgs = await orgsService.list();
          if (orgs.length > 0) {
            const first = orgs[0];
            setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
          }
        } catch {
          // ignore — org auto-select is best-effort
        }
      }
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: ({
      email,
      password,
      fullName,
    }: {
      email: string;
      password: string;
      fullName: string;
    }) => authService.register(email, password, fullName),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);
  return () => {
    authService.logout();
    setActiveOrg(null);
    queryClient.clear();
    router.push("/auth/login");
  };
}
