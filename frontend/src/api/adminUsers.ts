import { api } from "./client";

export type AdminUserRow = {
  id: number;
  email: string;
  name?: string | null;
  roles: string[];
  created_at?: string | null;
  subscription_tier?: string | null;
};

export type ListUsersParams = {
  q?: string;
  role?: string;
  sort_by?: "created_at" | "email" | "role";
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export type PagedUsers = {
  items: AdminUserRow[];
  total: number;
  page: number;
  page_size: number;
};

export async function listUsers(params?: ListUsersParams): Promise<PagedUsers> {
  const res = await api.get<PagedUsers>("/admin/users", { params });
  return res.data;
}

export async function setUserRoles(userId: number, roles: string[]) {
  const res = await api.put(`/admin/users/${userId}/roles`, { roles });
  return res.data;
}