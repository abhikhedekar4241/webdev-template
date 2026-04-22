import { CheckCircle2, Clock, AlertCircle, Circle } from "lucide-react";

const STATUS_ICON = {
  done: { icon: CheckCircle2, className: "text-emerald-500" },
  pending: { icon: Clock, className: "text-amber-500" },
  error: { icon: AlertCircle, className: "text-red-500" },
  info: { icon: Circle, className: "text-blue-500" },
} as const;

type ActivityStatus = keyof typeof STATUS_ICON;

interface ActivityItem {
  id: number;
  title: string;
  subtitle: string;
  time: string;
  status: ActivityStatus;
  badge?: string;
}

const activity: ActivityItem[] = [
  {
    id: 1,
    title: "New user registered",
    subtitle: "alice@example.com joined via invite",
    time: "2 min ago",
    status: "done",
    badge: "User",
  },
  {
    id: 2,
    title: "Payment processed",
    subtitle: "Invoice #1042 — $249.00",
    time: "14 min ago",
    status: "done",
    badge: "Billing",
  },
  {
    id: 3,
    title: "Background job failed",
    subtitle: "cleanup_expired_invitations — timeout",
    time: "32 min ago",
    status: "error",
    badge: "Worker",
  },
  {
    id: 4,
    title: "Export requested",
    subtitle: "users_export.csv — generating",
    time: "1 hr ago",
    status: "pending",
    badge: "Export",
  },
  {
    id: 5,
    title: "Org settings updated",
    subtitle: "demo-org slug changed by Admin User",
    time: "2 hr ago",
    status: "info",
    badge: "Org",
  },
  {
    id: 6,
    title: "File uploaded",
    subtitle: "report_q4.pdf (2.4 MB)",
    time: "3 hr ago",
    status: "done",
    badge: "Files",
  },
];

export function ActivityFeed() {
  return (
    <div className="divide-y divide-border">
      {activity.map((item) => {
        const { icon: Icon, className } = STATUS_ICON[item.status];
        return (
          <div key={item.id} className="flex items-start gap-3 px-5 py-3.5">
            <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${className}`} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate text-sm font-medium">{item.title}</p>
                {item.badge && (
                  <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                    {item.badge}
                  </span>
                )}
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.subtitle}</p>
            </div>
            <span className="shrink-0 text-[11px] text-muted-foreground">{item.time}</span>
          </div>
        );
      })}
    </div>
  );
}
