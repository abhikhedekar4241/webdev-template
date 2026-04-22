import { components } from "@/types/api";
import api from "./api";

export type SystemStats = components["schemas"]["SystemStats"];
export type UserListResponse = components["schemas"]["UserListResponse"];
export type OrgListResponse = components["schemas"]["OrgListResponse"];
export type ImpersonateResponse = components["schemas"]["ImpersonateResponse"];
export type AdminUser = UserListResponse["items"][number];
export type AdminOrg = OrgListResponse["items"][number];

export const adminService = {
  getStats: () => api.get<SystemStats>("/api/v1/admin/stats"),
  listUsers: (params: {
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: "asc" | "desc";
    search?: string;
  }) => api.get<UserListResponse>("/api/v1/admin/users", { params }),
  listOrgs: (params: {
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: "asc" | "desc";
    search?: string;
  }) => api.get<OrgListResponse>("/api/v1/admin/orgs", { params }),
  impersonate: (userId: string) =>
    api.post<ImpersonateResponse>(`/api/v1/admin/impersonate/${userId}`),
};
