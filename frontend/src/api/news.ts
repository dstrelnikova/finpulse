import { api } from "./client";

export type Impact = "positive" | "neutral" | "negative";
export type Confidence = "low" | "medium" | "high";

export type NewsIndicator = {
  impact: Impact;
  confidence: Confidence;
  importance?: Confidence | null;
  rationale: string[];
};

export type NewsItem = {
  id: string | number;
  slug: string;
  title: string;
  source: string;
  url: string;
  summary: string;
  bullets: string[];
  conclusion: string | null;
  market_meaning?: string | null;
  affected_segments?: string[];
  risks: string[];
  indicator: NewsIndicator | null;
  asof: string | null;
};

export async function getNewsFeed(): Promise<NewsItem[]> {
  const res = await api.get<NewsItem[]>("/news/feed");
  return res.data;
}

export async function getNewsItem(id: string | number): Promise<NewsItem> {
  const res = await api.get<NewsItem>(`/news/${encodeURIComponent(String(id))}`);
  return res.data;
}

export async function getPublicNewsFeed(limit = 50): Promise<NewsItem[]> {
  const res = await api.get<NewsItem[]>("/public/news", {
    params: { limit },
  });
  return res.data;
}

export async function getPublicNewsItemBySlug(slug: string): Promise<NewsItem> {
  const res = await api.get<NewsItem>(`/public/news/slug/${encodeURIComponent(slug)}`);
  return res.data;
}
