import { api } from "./client";

export type InvestmentHorizon = "short" | "mid" | "long";
export type ExperienceLevel = "beginner" | "intermediate" | "pro";
export type RiskLevel = "low" | "medium" | "high";

export interface ProfileData {
  id: number;
  name: string;
  email: string;

  market: "RU";

  investment_horizon?: InvestmentHorizon | null;
  experience_level?: ExperienceLevel | null;
  risk_level?: RiskLevel | null;

  tickers: string[];
  sectors: string[];
}

export interface ProfileUpdatePayload {
  investment_horizon?: InvestmentHorizon | null;
  experience_level?: ExperienceLevel | null;
  risk_level?: RiskLevel | null;
  tickers?: string[];
  sectors?: string[];
}

export async function getProfile(): Promise<ProfileData> {
  const res = await api.get<ProfileData>("/profile");
  return res.data;
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<ProfileData> {
  const res = await api.patch<ProfileData>("/profile", payload);
  return res.data;
}
