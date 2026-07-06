import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function getAccessToken() {
  return localStorage.getItem("accessToken");
}

export function getRefreshToken() {
  return localStorage.getItem("refreshToken");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("accessToken", access);
  localStorage.setItem("refreshToken", refresh);
}

export function clearTokens() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
}

export const api = axios.create({
  baseURL: API_URL,
  timeout: 190_000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let pendingRequests: ((token: string | null) => void)[] = [];

async function refreshTokens() {
  if (isRefreshing) {
    return new Promise<string | null>((resolve) => {
      pendingRequests.push(resolve);
    });
  }

  isRefreshing = true;

  try {
    const refresh = getRefreshToken();
    if (!refresh) {
      throw new Error("No refresh token");
    }

    const response = await axios.post(`${API_URL}/auth/refresh`, {
      refresh_token: refresh,
    });

    const { access_token, refresh_token } = response.data;
    setTokens(access_token, refresh_token);

    pendingRequests.forEach((cb) => cb(access_token));
    pendingRequests = [];

    return access_token;
  } catch (err) {
    clearTokens();
    pendingRequests.forEach((cb) => cb(null));
    pendingRequests = [];
    return null;
  } finally {
    isRefreshing = false;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    const newToken = await refreshTokens();

    if (!newToken) {
      return Promise.reject(error);
    }

    originalRequest.headers = originalRequest.headers ?? {};
    originalRequest.headers.Authorization = `Bearer ${newToken}`;
    return api(originalRequest);
  }
);
