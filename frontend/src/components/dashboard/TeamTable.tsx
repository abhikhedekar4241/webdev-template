import { MoreHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const tableUsers = [
  {
    name: "Alice Martin",
    email: "alice@example.com",
    role: "Admin",
    status: "Active",
    joined: "Apr 12, 2026",
  },
  {
    name: "Bob Chen",
    email: "bob@example.com",
    role: "Member",
    status: "Active",
    joined: "Apr 14, 2026",
  },
  {
    name: "Carol Davis",
    email: "carol@example.com",
    role: "Member",
    status: "Invited",
    joined: "Apr 18, 2026",
  },
  {
    name: "Dan Kim",
    email: "dan@example.com",
    role: "Admin",
    status: "Active",
    joined: "Mar 30, 2026",
  },
  {
    name: "Eve Santos",
    email: "eve@example.com",
    role: "Member",
    status: "Inactive",
    joined: "Mar 10, 2026",
  },
];

const STATUS_BADGE: Record<string, "success" | "warning" | "secondary"> = {
  Active: "success",
  Invited: "warning",
  Inactive: "secondary",
};

export function TeamTable() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Name</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Role</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">
              Status
            </th>
            <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">
              Joined
            </th>
            <th className="px-5 py-3" />
          </tr>
        </thead>
        <tbody>
          {tableUsers.map((u, i) => (
            <tr
              key={u.email}
              className={`${i > 0 ? "border-t border-border" : ""} transition-colors hover:bg-muted/30`}
            >
              <td className="px-5 py-3.5">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {u.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </div>
                  <div>
                    <p className="font-medium">{u.name}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </div>
                </div>
              </td>
              <td className="px-5 py-3.5">
                <Badge variant={u.role === "Admin" ? "admin" : "member"}>{u.role}</Badge>
              </td>
              <td className="px-5 py-3.5">
                <Badge variant={STATUS_BADGE[u.status]}>{u.status}</Badge>
              </td>
              <td className="px-5 py-3.5 text-sm text-muted-foreground">{u.joined}</td>
              <td className="px-5 py-3.5">
                <button className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted">
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
