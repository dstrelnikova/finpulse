import axios from "axios";

type ApiErrorDetail = string | { msg?: string } | Array<string | { msg?: string }>;
type ErrorLike = { response?: { status?: number; data?: { detail?: ApiErrorDetail } } };

function stringifyDetail(detail: ApiErrorDetail): string {
  if (Array.isArray(detail)) {
    return detail.map((item) => (typeof item === "string" ? item : item.msg ?? JSON.stringify(item))).join("; ");
  }
  if (typeof detail === "string") return detail;
  return detail.msg ?? JSON.stringify(detail);
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error) && !isErrorLike(error)) return fallback;

  const detail = (error as ErrorLike).response?.data?.detail;
  return detail ? stringifyDetail(detail) : fallback;
}

export function getApiErrorDetail(error: unknown): string | undefined {
  if (!axios.isAxiosError(error) && !isErrorLike(error)) return undefined;

  const detail = (error as ErrorLike).response?.data?.detail;
  return typeof detail === "string" ? detail : undefined;
}

export function getApiErrorStatus(error: unknown): number | undefined {
  if (!axios.isAxiosError(error) && !isErrorLike(error)) return undefined;
  return (error as ErrorLike).response?.status;
}

function isErrorLike(error: unknown): error is ErrorLike {
  return typeof error === "object" && error !== null && "response" in error;
}
