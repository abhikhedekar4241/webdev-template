import axios from "axios";
import { ROUTES } from "@/constants/routes";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
      window.location.href = ROUTES.auth.login;
    }
    return Promise.reject(error);
  }
);

/**
 * Persist the access token in both localStorage (for API requests) and a
 * cookie (for Next.js edge middleware route protection). Call this on login.
 */
export function setToken(token: string): void {
  localStorage.setItem("access_token", token);
  document.cookie = `access_token=${token}; path=/; SameSite=Lax`;
}

/**
 * Remove the access token from localStorage and the cookie. Call this on logout.
 * The 401 interceptor above also calls this automatically.
 */
export function clearToken(): void {
  localStorage.removeItem("access_token");
  document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
}

export default api;
