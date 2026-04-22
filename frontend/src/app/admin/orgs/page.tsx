"use client";

import * as React from "react";
import { useAdminOrgs } from "@/queries/admin";
import { Building2, Globe, Calendar } from "lucide-react";
import { format } from "date-fns";
import { DataTable } from "@/components/shared/DataTable";
import { ColumnDef, SortingState, PaginationState, ColumnFiltersState } from "@tanstack/react-table";
import { AdminOrg } from "@/services/admin";

export default function AdminOrgsPage() {
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);

  const search = (columnFilters.find((f) => f.id === "search")?.value as string) || "";
  const sortBy = sorting.length > 0 ? sorting[0].id : undefined;
  const sortOrder = sorting.length > 0 ? (sorting[0].desc ? "desc" : "asc") : undefined;

  const { data: orgsData, isLoading } = useAdminOrgs({
    skip: pagination.pageIndex * pagination.pageSize,
    limit: pagination.pageSize,
    sort_by: sortBy,
    sort_order: sortOrder as "asc" | "desc",
    search: search,
  });

  const columns = React.useMemo<ColumnDef<AdminOrg>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Organization",
        cell: ({ row }) => {
          const org = row.original;
          return (
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <div className="font-medium">{org.name}</div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="font-mono text-[10px] bg-muted px-1 rounded">{org.id.slice(0, 8)}...</span>
                </div>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "slug",
        header: "Slug",
        cell: ({ row }) => (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Globe className="h-3.5 w-3.5" />
            {row.getValue("slug")}
          </div>
        ),
      },
      {
        accessorKey: "created_at",
        header: () => <div className="text-right">Created</div>,
        cell: ({ row }) => {
          const org = row.original;
          return (
            <div className="text-right text-muted-foreground">
              <div className="flex flex-col items-end">
                <div className="flex items-center gap-1.5 text-xs">
                  <Calendar className="h-3 w-3" />
                  {format(new Date(org.created_at), "MMM d, yyyy")}
                </div>
                <div className="text-[10px] opacity-70">
                  By: {org.created_by.slice(0, 8)}...
                </div>
              </div>
            </div>
          );
        },
      },
    ],
    []
  );

  const pageCount = Math.ceil((orgsData?.total || 0) / pagination.pageSize);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Organization Management</h2>
        <p className="text-muted-foreground">View and manage all organizations in the system.</p>
      </div>

      <DataTable
        columns={columns}
        data={orgsData?.items || []}
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
            placeholder: "Search organizations...",
            type: "text",
          },
        ]}
      />
    </div>
  );
}
