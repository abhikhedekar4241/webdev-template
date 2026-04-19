export const QUERY_KEYS = {
  me: ["me"] as const,
  orgs: {
    list: ["orgs"] as const,
    detail: (orgId: string) => ["orgs", orgId] as const,
    members: (orgId: string) => ["orgs", orgId, "members"] as const,
    flags: (orgId: string) => ["orgs", orgId, "flags"] as const,
  },
  invitations: {
    list: ["invitations"] as const,
  },
  files: {
    list: (orgId: string) => ["files", orgId] as const,
  },
} as const;
