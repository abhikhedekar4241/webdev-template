export const ROUTES = {
  home: "/",
  dashboard: "/dashboard",
  auth: {
    login: "/auth/login",
    signup: "/auth/signup",
    forgotPassword: "/auth/forgot-password",
    resetPassword: "/auth/reset-password",
  },
  orgs: {
    list: "/orgs",
    new: "/orgs/new",
    detail: (orgId: string) => `/orgs/${orgId}`,
    members: (orgId: string) => `/orgs/${orgId}/members`,
    settings: (orgId: string) => `/orgs/${orgId}/settings`,
  },
  invitations: "/invitations",
} as const;
