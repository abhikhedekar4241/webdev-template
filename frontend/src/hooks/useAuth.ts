"use client";

import { useMemo } from "react";

interface AuthUser {
  id: string;
}

/**
 * Returns the currently authenticated user by decoding the JWT stored in
 * localStorage.  Returns null when no token is present or the token is
 * malformed.
 */
export function useAuth(): { user: AuthUser | null } {
  const user = useMemo<AuthUser | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return null;
      const payload = JSON.parse(atob(token.split(".")[1]));
      const id: string = payload.sub ?? payload.user_id ?? payload.id ?? "";
      return id ? { id } : null;
    } catch {
      return null;
    }
  }, []);

  return { user };
}
