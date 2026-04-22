import { Suspense } from "react";
import AuthCallbackInner from "./AuthCallbackInner";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <p className="text-sm text-muted-foreground">Signing you in…</p>
        </div>
      }
    >
      <AuthCallbackInner />
    </Suspense>
  );
}
