import { api } from "./client";

export type Me = {
  id: number;
  email: string;
  roles: string[];
  permissions: string[];
};

export async function getMe(): Promise<Me> {
  const res = await api.get<Me>("/me");
  return res.data;
}