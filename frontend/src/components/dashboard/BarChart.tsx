const chartData = [
  { month: "Jan", value: 40 },
  { month: "Feb", value: 62 },
  { month: "Mar", value: 55 },
  { month: "Apr", value: 78 },
  { month: "May", value: 90 },
  { month: "Jun", value: 72 },
  { month: "Jul", value: 85 },
  { month: "Aug", value: 95 },
  { month: "Sep", value: 68 },
  { month: "Oct", value: 80 },
  { month: "Nov", value: 74 },
  { month: "Dec", value: 88 },
];

export function BarChart() {
  const max = Math.max(...chartData.map((d) => d.value));
  return (
    <div className="flex h-40 items-end gap-1.5">
      {chartData.map((d) => (
        <div key={d.month} className="group flex flex-1 flex-col items-center gap-1">
          <div
            className="relative w-full rounded-t-md bg-primary/20 transition-all group-hover:bg-primary/40"
            style={{ height: `${(d.value / max) * 100}%` }}
          >
            <div
              className="absolute inset-x-0 bottom-0 rounded-t-md bg-primary transition-all"
              style={{ height: "60%" }}
            />
            {/* Tooltip */}
            <span className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-foreground px-1.5 py-0.5 text-[10px] font-medium text-background opacity-0 transition-opacity group-hover:opacity-100">
              {d.value}
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground">{d.month}</span>
        </div>
      ))}
    </div>
  );
}
