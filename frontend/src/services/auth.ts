import api, { setToken, clearToken } from "./api";

export interface UserData {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export const authService = {
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const { data } = await api.post<{ access_token: string }>("/api/v1/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    setToken(data.access_token);
    return data.access_token;
  },

  async register(email: string, password: string, fullName: string): Promise<UserData> {
    const { data } = await api.post<UserData>("/api/v1/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    return data;
  },

  async verifyEmail(email: string, otp: string): Promise<string> {
    const { data } = await api.post<{ access_token: string }>("/api/v1/auth/verify-email", {
      email,
      otp,
    });
    setToken(data.access_token);
    return data.access_token;
  },

  async resendVerification(email: string): Promise<void> {
    await api.post("/api/v1/auth/resend-verification", { email });
  },

  async me(): Promise<UserData> {
    const { data } = await api.get<UserData>("/api/v1/auth/me");
    return data;
  },

  logout(): void {
    clearToken();
  },
};
