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
      localStorage.removeItem("access_token");
      // Also clear auth cookie for middleware
      document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
      window.location.href = ROUTES.auth.login;
    }
    return Promise.reject(error);
  }
);

export default api;
