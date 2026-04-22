import api from "./api";
import { components } from "@/types/api";

export type NotificationData = components["schemas"]["NotificationResponse"];
type NotificationResponse = NotificationData;

export const notificationsService = {
  list: (unreadOnly = false) =>
    api
      .get<NotificationResponse[]>("/api/v1/notifications/", { params: { unread_only: unreadOnly } }),

  markAsRead: (id: string) =>
    api.patch<NotificationResponse>(`/api/v1/notifications/${id}/read`),

  markAllAsRead: () => api.post("/api/v1/notifications/read-all"),
};
