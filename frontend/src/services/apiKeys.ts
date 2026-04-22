import api from "./api";
import { components } from "@/types/api";

type ApiKeyResponse = components["schemas"]["ApiKeyResponse"];
export type ApiKeyCreated = components["schemas"]["ApiKeyCreated"];
type ApiKeyCreate = components["schemas"]["ApiKeyCreate"];

export const apiKeysService = {
  list: (orgId: string) => api.get<ApiKeyResponse[]>(`/api/v1/orgs/${orgId}/api-keys`),

  create: (orgId: string, name: string) =>
    api.post<ApiKeyCreated>(`/api/v1/orgs/${orgId}/api-keys`, { name } as ApiKeyCreate),

  revoke: (orgId: string, keyId: string) => api.delete(`/api/v1/orgs/${orgId}/api-keys/${keyId}`),
};
