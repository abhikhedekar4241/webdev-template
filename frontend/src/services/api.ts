import { ROUTES } from "@/constants/routes";

interface RequestConfig extends Omit<RequestInit, "body"> {
  params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", token);
    const secure =
      typeof location !== "undefined" && location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `access_token=${token}; path=/; SameSite=Lax${secure}`;
  }
}

export function clearToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
  }
}

async function fetchWrapper<T>(url: string, config: RequestConfig = {}): Promise<T> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || "";
  let fullUrl = `${baseURL}${url}`;

  if (config.params) {
    const searchParams = new URLSearchParams();
    Object.entries(config.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const qs = searchParams.toString();
    if (qs) {
      fullUrl += fullUrl.includes("?") ? `&${qs}` : `?${qs}`;
    }
  }

  const headers: Record<string, string> = { ...config.headers };

  if (config.body instanceof FormData) {
    const contentTypeKey = Object.keys(headers).find((k) => k.toLowerCase() === "content-type");
    if (contentTypeKey && headers[contentTypeKey] === "multipart/form-data") {
      delete headers[contentTypeKey];
    }
  } else if (!headers["Content-Type"] && !(config.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let body = config.body;
  if (
    body &&
    !(body instanceof FormData || body instanceof URLSearchParams) &&
    typeof body === "object"
  ) {
    body = JSON.stringify(body);
  }

  const response = await fetch(fullUrl, {
    ...config,
    headers,
    body,
  });

  if (!response.ok) {
    const errorData = await response.text().catch(() => "");
    let parsedError;
    try {
      parsedError = JSON.parse(errorData);
    } catch {
      parsedError = errorData;
    }

    const error = {
      response: {
        status: response.status,
        data: parsedError,
      },
    };

    if (response.status === 401 && typeof window !== "undefined") {
      clearToken();
      window.location.href = ROUTES.auth.login;
    }

    return Promise.reject(error);
  }

  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

const api = {
  get: <T>(url: string, config?: RequestConfig) =>
    fetchWrapper<T>(url, { ...config, method: "GET" }),
  post: <T>(url: string, data?: any, config?: RequestConfig) =>
    fetchWrapper<T>(url, { ...config, method: "POST", body: data }),
  put: <T>(url: string, data?: any, config?: RequestConfig) =>
    fetchWrapper<T>(url, { ...config, method: "PUT", body: data }),
  patch: <T>(url: string, data?: any, config?: RequestConfig) =>
    fetchWrapper<T>(url, { ...config, method: "PATCH", body: data }),
  delete: <T>(url: string, config?: RequestConfig) =>
    fetchWrapper<T>(url, { ...config, method: "DELETE" }),
};

export default api;
