import { api } from "./client";

export type MoexQuote = {
  ticker: string;
  short_name: string | null;
  last: number | null;
  change: number | null;
  change_percent: number | null;
  update_time: string | null;
  currency: string;
};

export type MoexQuotesResponse = {
  index: string;
  source: string;
  fetched_at: string;
  fallback: boolean;
  items: MoexQuote[];
};

export async function getImoexQuotes(limit = 12): Promise<MoexQuotesResponse> {
  const res = await api.get<MoexQuotesResponse>("/public/moex/imoex/quotes", {
    params: { limit },
  });
  return res.data;
}
