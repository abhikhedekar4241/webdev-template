import api from "./api";
import { components } from "@/types/api";

type FileResponse = components["schemas"]["FileResponse"];
type PresignedUrlResponse = components["schemas"]["PresignedUrlResponse"];

export const filesService = {
  upload: (orgId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<FileResponse>(`/api/v1/files/?org_id=${orgId}`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
  },

  getUrl: (fileId: string) =>
    api
      .get<PresignedUrlResponse>(`/api/v1/files/${fileId}/url`)
      .then((r) => r.url),

  delete: (fileId: string) => api.delete(`/api/v1/files/${fileId}`),
};
