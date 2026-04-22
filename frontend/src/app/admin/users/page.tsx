"use client";

import * as React from "react";
import { useAdminUsers, useImpersonate } from "@/queries/admin";
import { UserCircle, ShieldCheck, Mail, LogIn } from "lucide-react";
import { DataTable } from "@/components/shared/DataTable";
import {
  ColumnDef,
  SortingState,
  PaginationState,
  ColumnFiltersState,
} from "@tanstack/react-table";
import { AdminUser } from "@/services/admin";
import { Button } from "@/components/ui/button";

export default function AdminUsersPage() {
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);

  const search = (columnFilters.find((f) => f.id === "search")?.value as string) || "";
  const sortBy = sorting.length > 0 ? sorting[0].id : undefined;
  const sortOrder = sorting.length > 0 ? (sorting[0].desc ? "desc" : "asc") : undefined;

  const { data: usersData, isLoading } = useAdminUsers({
    skip: pagination.pageIndex * pagination.pageSize,
    limit: pagination.pageSize,
    sort_by: sortBy,
    sort_order: sortOrder as "asc" | "desc",
    search: search,
  });

  const impersonate = useImpersonate();

  const columns = React.useMemo<ColumnDef<AdminUser>[]>(
    () => [
      {
        accessorKey: "full_name",
        header: "User",
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                {user.is_superuser ? (
                  <ShieldCheck className="h-5 w-5" />
                ) : (
                  <UserCircle className="h-5 w-5" />
                )}
              </div>
              <div>
                <div className="font-medium">{user.full_name}</div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Mail className="h-3 w-3" />
                  {user.email}
                </div>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "is_active",
        header: "Status",
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className="flex flex-col gap-1">
              <span
                className={`inline-flex w-fit items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  user.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                }`}
              >
                {user.is_active ? "Active" : "Inactive"}
              </span>
              {!user.is_verified && (
                <span className="text-[10px] font-medium text-amber-600">Unverified email</span>
              )}
            </div>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right">Actions</div>,
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className="text-right">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (
                    confirm(`Impersonate ${user.full_name}? Your current session will be replaced.`)
                  ) {
                    impersonate.mutate(user.id);
                  }
                }}
                disabled={impersonate.isPending}
                className="gap-1.5 text-xs"
              >
                <LogIn className="h-3.5 w-3.5" />
                Login As
              </Button>
            </div>
          );
        },
      },
    ],
    [impersonate]
  );

  const pageCount = Math.ceil((usersData?.total || 0) / pagination.pageSize);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">User Management</h2>
        <p className="text-muted-foreground">
          Manage all registered users and impersonate accounts for debugging.
        </p>
      </div>

      <DataTable
        columns={columns}
        data={usersData?.items || []}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        sorting={sorting}
        onSortingChange={setSorting}
        columnFilters={columnFilters}
        onColumnFiltersChange={setColumnFilters}
        isLoading={isLoading}
        filterConfigs={[
          {
            id: "search",
            placeholder: "Search users...",
            type: "text",
          },
        ]}
      />
    </div>
  );
}
