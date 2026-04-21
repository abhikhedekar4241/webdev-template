import api from "./api";

export interface InvitationData {
  id: string;
  org_id: string;
  invited_email: string;
  role: "owner" | "admin" | "member";
  status: "pending" | "accepted" | "declined";
  expires_at: string;
  created_at: string;
}

export const invitationsService = {
  list: () =>
    api.get<InvitationData[]>("/v1/invitations/").then((r) => r.data),

  create: (data: { org_id: string; email: string; role: string }) =>
    api.post<InvitationData>("/v1/invitations/", data).then((r) => r.data),

  accept: (invId: string) =>
    api
      .post<{ message: string }>(`/v1/invitations/${invId}/accept`)
      .then((r) => r.data),

  decline: (invId: string) =>
    api
      .post<{ message: string }>(`/v1/invitations/${invId}/decline`)
      .then((r) => r.data),
};
