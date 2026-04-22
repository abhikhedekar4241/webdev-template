export default function Page() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-24 text-center">
      <div className="rounded-full bg-muted p-4">
        <div className="h-8 w-8 rounded bg-muted-foreground/20" />
      </div>
      <h2 className="text-lg font-semibold capitalize">analytics</h2>
      <p className="max-w-xs text-sm text-muted-foreground">
        This section is a placeholder. Wire up your own content here.
      </p>
    </div>
  );
}
