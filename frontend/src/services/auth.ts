import api, { setToken, clearToken } from "./api";
import { components } from "@/types/api";

type UserResponse = components["schemas"]["UserResponse"];
type TokenResponse = components["schemas"]["TokenResponse"];
type RegisterRequest = components["schemas"]["RegisterRequest"];
type VerifyEmailRequest = components["schemas"]["VerifyEmailRequest"];
type ResendVerificationRequest = components["schemas"]["ResendVerificationRequest"];
type OnboardingRequest = components["schemas"]["OnboardingRequest"];

export const authService = {
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const data = await api.post<TokenResponse>("/api/v1/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    setToken(data.access_token);
    return data.access_token;
  },

  async register(email: string, password: string, fullName: string): Promise<UserResponse> {
    const data = await api.post<UserResponse>("/api/v1/auth/register", {
      email,
      password,
      full_name: fullName,
    } as RegisterRequest);
    return data;
  },

  async verifyEmail(email: string, otp: string): Promise<string> {
    const data = await api.post<TokenResponse>("/api/v1/auth/verify-email", {
      email,
      otp,
    } as VerifyEmailRequest);
    setToken(data.access_token);
    return data.access_token;
  },

  async resendVerification(email: string): Promise<void> {
    await api.post("/api/v1/auth/resend-verification", { email } as ResendVerificationRequest);
  },

  async me(): Promise<UserResponse> {
    const data = await api.get<UserResponse>("/api/v1/auth/me");
    return data;
  },

  async completeOnboarding(fullName: string, orgName: string): Promise<UserResponse> {
    const data = await api.post<UserResponse>("/api/v1/auth/onboarding", {
      full_name: fullName,
      org_name: orgName,
    } as OnboardingRequest);
    return data;
  },

  logout(): void {
    clearToken();
  },
};
