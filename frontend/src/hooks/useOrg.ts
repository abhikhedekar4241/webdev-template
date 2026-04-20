import { useOrgStore } from "@/store/org";

export function useOrg() {
  const activeOrg = useOrgStore((state) => state.activeOrg);
  const setActiveOrg = useOrgStore((state) => state.setActiveOrg);
  return { activeOrg, setActiveOrg };
}
