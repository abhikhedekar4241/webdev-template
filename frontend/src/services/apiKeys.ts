import api from "./api";

export interface ApiKeyData {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface ApiKeyCreated extends ApiKeyData {
  key: string; // full raw key — available only at creation time
}

export const apiKeysService = {
  list: (orgId: string) =>
    api
      .get<ApiKeyData[]>(`/api/v1/orgs/${orgId}/api-keys`)
      .then((r) => r.data),

  create: (orgId: string, name: string) =>
    api
      .post<ApiKeyCreated>(`/api/v1/orgs/${orgId}/api-keys`, { name })
      .then((r) => r.data),

  revoke: (orgId: string, keyId: string) =>
    api.delete(`/api/v1/orgs/${orgId}/api-keys/${keyId}`),
};
