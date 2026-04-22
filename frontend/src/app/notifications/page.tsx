"use client";

import { Bell, Check, Mail } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { AppShell } from "@/components/shared/AppShell";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
} from "@/queries/notifications";
import { useInvitations } from "@/queries/invitations";
import { NotificationData } from "@/services/notifications";
import { InvitationCard } from "@/components/shared/InvitationCard";

export default function NotificationsPage() {
  const { data: notifications, isLoading: notificationsLoading } = useNotifications();
  const { data: invitations, isLoading: invitationsLoading } = useInvitations();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const isLoading = notificationsLoading || invitationsLoading;
  const unreadCount = notifications?.filter((n) => !n.read_at).length || 0;

  function renderNotificationContent(notification: NotificationData) {
    switch (notification.type) {
      case "org_invitation":
        // For notifications, we still show the simple text-based invitation if it's already accepted/declined
        const status = notification.data.invitation_status;
        if (status !== "pending") {
          return (
            <div className="space-y-1">
              <p className="text-sm">
                Invitation to join <span className="font-semibold">{notification.data.org_name}</span>.
              </p>
              <div className="flex items-center gap-2 text-xs font-medium">
                {status === "accepted" && <span className="text-green-600 flex items-center gap-1">Accepted</span>}
                {status === "declined" && <span className="text-red-600 flex items-center gap-1">Declined</span>}
                {status === "expired" && <span className="text-amber-600">Expired</span>}
              </div>
            </div>
          );
        }
        
        // Find the actual pending invitation to show the rich card
        const invitation = invitations?.find(i => i.id === notification.data.invitation_id);
        if (invitation) {
          return <div className="mt-2"><InvitationCard invitation={invitation} /></div>;
        }

        return (
          <p className="text-sm text-muted-foreground italic">
            This invitation to {notification.data.org_name} is no longer pending.
          </p>
        );
      default:
        return <p className="text-sm">{String(notification.data?.message || "System notification.")}</p>;
    }
  }

  function getIcon(type: string) {
    switch (type) {
      case "org_invitation":
        return <Mail className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-muted-foreground text-sm">
            {unreadCount > 0 ? `You have ${unreadCount} unread messages.` : "Your inbox is clear."}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={() => markAllRead.mutate()}
            className="text-xs font-medium text-primary hover:underline"
          >
            Mark all as read
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {notifications?.map((notification) => (
            <div
              key={notification.id}
              className={`group relative flex gap-4 rounded-xl border p-4 transition-all hover:bg-muted/30 ${
                !notification.read_at ? "border-primary/20 bg-primary/5 shadow-sm" : "border-border bg-card"
              }`}
            >
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                  !notification.read_at ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                }`}
              >
                {getIcon(notification.type)}
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">
                    {notification.type.replace("_", " ")}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                  </span>
                </div>
                {renderNotificationContent(notification)}
              </div>

              {!notification.read_at && (
                <button
                  onClick={() => markRead.mutate(notification.id)}
                  className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:text-primary"
                  title="Mark as read"
                >
                  <Check className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}

          {notifications?.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center space-y-4 border-2 border-dashed rounded-2xl border-border">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                <Bell className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-semibold">No notifications</h3>
                <p className="text-sm text-muted-foreground">We&apos;ll notify you when something important happens.</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
