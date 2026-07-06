import { api, setTokens, clearTokens } from "./client";

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function registerUser(data: RegisterPayload) {
  const response = await api.post("/auth/register", data);
  return response.data;
}

export async function loginUser(data: LoginPayload) {
  const response = await api.post("/auth/login", data);
  return response.data as { access_token: string; refresh_token: string };
}

export async function logoutUser() {
  try {
    await api.post("/auth/logout");
  } finally {
    clearTokens();
  }
}
