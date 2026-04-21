export function getApiError(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  return fallback;
}
