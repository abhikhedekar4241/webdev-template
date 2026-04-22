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
    detail: (slug: string) => `/orgs/${slug}`,
    members: (slug: string) => `/orgs/${slug}/members`,
    settings: (slug: string) => `/orgs/${slug}/settings`,
  },
  invitations: "/notifications",
} as const;
