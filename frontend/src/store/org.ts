import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ActiveOrg {
  id: string;
  name: string;
  slug: string;
}

interface OrgState {
  activeOrg: ActiveOrg | null;
  setActiveOrg: (org: ActiveOrg | null) => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      activeOrg: null,
      setActiveOrg: (org) => set({ activeOrg: org }),
    }),
    { name: "org-storage" }
  )
);
