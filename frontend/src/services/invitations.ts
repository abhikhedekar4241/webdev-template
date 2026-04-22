import api from "./api";
import { components } from "@/types/api";

type InvitationResponse = components["schemas"]["InvitationResponse"];
type InvitationCreate = components["schemas"]["InvitationCreate"];
type MessageResponse = components["schemas"]["MessageResponse"];

export const invitationsService = {
  list: () => api.get<InvitationResponse[]>("/api/v1/invitations/"),

  create: (data: InvitationCreate) =>
    api.post<InvitationResponse>("/api/v1/invitations/", data),

  accept: (invId: string) =>
    api.post<MessageResponse>(`/api/v1/invitations/${invId}/accept`),

  decline: (invId: string) =>
    api.post<MessageResponse>(`/api/v1/invitations/${invId}/decline`),
};
