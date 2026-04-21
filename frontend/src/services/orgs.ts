import api from "./api";

export interface OrgData {
  id: string;
  name: string;
  slug: string;
  created_by: string;
  created_at: string;
}

export interface MembershipData {
  user_id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

export const orgsService = {
  list: () => api.get<OrgData[]>("/api/v1/orgs/").then((r) => r.data),

  get: (orgId: string) =>
    api.get<OrgData>(`/api/v1/orgs/${orgId}`).then((r) => r.data),

  create: (data: { name: string; slug: string }) =>
    api.post<OrgData>("/api/v1/orgs/", data).then((r) => r.data),

  update: (orgId: string, data: { name?: string; slug?: string }) =>
    api.patch<OrgData>(`/api/v1/orgs/${orgId}`, data).then((r) => r.data),

  delete: (orgId: string) => api.delete(`/api/v1/orgs/${orgId}`),

  listMembers: (orgId: string) =>
    api
      .get<MembershipData[]>(`/api/v1/orgs/${orgId}/members`)
      .then((r) => r.data),

  changeMemberRole: (orgId: string, userId: string, role: string) =>
    api
      .patch<MembershipData>(`/api/v1/orgs/${orgId}/members/${userId}`, { role })
      .then((r) => r.data),

  removeMember: (orgId: string, userId: string) =>
    api.delete(`/api/v1/orgs/${orgId}/members/${userId}`),
};
