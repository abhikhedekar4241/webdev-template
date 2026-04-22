"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Shield } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

import { useMe } from "@/queries/auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { data: me, isLoading } = useMe();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && (!me || !me.is_superuser)) {
      router.push("/dashboard");
    }
  }, [me, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-muted-foreground animate-pulse">Verifying privileges…</p>
      </div>
    );
  }

  if (!me || !me.is_superuser) {
    return null; // Will redirect via useEffect
  }

  const navItems = [
    { href: "/admin", label: "Dashboard" },
    { href: "/admin/users", label: "Users" },
    { href: "/admin/orgs", label: "Organizations" },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mini Admin Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col">
        <div className="h-14 flex items-center gap-2.5 px-6 border-b border-border">
          <Shield className="h-5 w-5 text-primary" />
          <span className="font-bold">System Admin</span>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "block px-3 py-2 rounded-md text-sm transition-colors",
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : "font-normal text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-border">
          <Link href="/dashboard" className="text-xs text-muted-foreground hover:text-foreground">
            ← Back to App
          </Link>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-border flex items-center px-8 bg-card justify-between">
          <h1 className="text-sm font-semibold">Admin Panel</h1>
          <div className="text-xs text-muted-foreground">Logged in as {me.full_name}</div>
        </header>
        <main className="flex-1 overflow-auto p-8">{children}</main>
      </div>
    </div>
  );
}
