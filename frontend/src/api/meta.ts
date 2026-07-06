import { api } from "./client";

export interface MetaOptions {
  markets: string[];
  categories: string[];
}

export async function getMetaOptions(): Promise<MetaOptions> {
  const res = await api.get<MetaOptions>("/meta/options");
  return res.data;
}
