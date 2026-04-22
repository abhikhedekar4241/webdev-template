import api from "./api";
import { components } from "@/types/api";

type NotificationResponse = components["schemas"]["NotificationResponse"];

export const notificationsService = {
  list: (unreadOnly = false) =>
    api
      .get<NotificationResponse[]>("/api/v1/notifications/", { params: { unread_only: unreadOnly } }),

  markAsRead: (id: string) =>
    api.patch<NotificationResponse>(`/api/v1/notifications/${id}/read`),

  markAllAsRead: () => api.post("/api/v1/notifications/read-all"),
};
