import api from "./api";

export interface FileData {
  id: string;
  org_id: string;
  uploaded_by: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export const filesService = {
  upload: (orgId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<FileData>(`/api/v1/files/?org_id=${orgId}`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },

  getUrl: (fileId: string) =>
    api
      .get<{ url: string }>(`/api/v1/files/${fileId}/url`)
      .then((r) => r.data.url),

  delete: (fileId: string) => api.delete(`/api/v1/files/${fileId}`),
};
