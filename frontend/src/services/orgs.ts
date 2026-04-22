import api from "./api";
import { components } from "@/types/api";

type OrgResponse = components["schemas"]["OrgResponse"];
type MembershipResponse = components["schemas"]["MembershipResponse"];
type OrgCreate = components["schemas"]["OrgCreate"];
type OrgUpdate = components["schemas"]["OrgUpdate"];

export const orgsService = {
  list: () => api.get<OrgResponse[]>("/api/v1/orgs/"),

  get: (orgId: string) => api.get<OrgResponse>(`/api/v1/orgs/${orgId}`),

  getBySlug: (slug: string) => api.get<OrgResponse>(`/api/v1/orgs/slug/${slug}`),

  create: (data: OrgCreate) => api.post<OrgResponse>("/api/v1/orgs/", data),

  update: (orgId: string, data: OrgUpdate) => api.patch<OrgResponse>(`/api/v1/orgs/${orgId}`, data),

  delete: (orgId: string) => api.delete(`/api/v1/orgs/${orgId}`),

  listMembers: (orgId: string) => api.get<MembershipResponse[]>(`/api/v1/orgs/${orgId}/members`),

  changeMemberRole: (orgId: string, userId: string, role: string) =>
    api.patch<MembershipResponse>(`/api/v1/orgs/${orgId}/members/${userId}`, {
      role,
    }),

  removeMember: (orgId: string, userId: string) =>
    api.delete(`/api/v1/orgs/${orgId}/members/${userId}`),
};
