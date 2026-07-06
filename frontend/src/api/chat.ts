import { api } from "./client";

export type ChatResponse = {
  answer: string;
  chat_id: number;
};

export type ChatHistoryItem = {
  id: number;
  role: "user" | "assistant" | "bot" | "FinPulse";
  content: string;
  created_at: string;
};

export type ChatSession = {
  id: number;
  title: string;
  topic?: string | null;
  is_default: boolean;
};

export async function sendChatMessage(payload: { message: string; chat_id?: number }): Promise<ChatResponse> {
  const res = await api.post("/chat/send", payload);
  return res.data;
}

export async function getChatHistory(limit = 50, chat_id?: number): Promise<ChatHistoryItem[]> {
  const res = await api.get("/chat/history", { params: { limit, chat_id } });
  return res.data;
}

export async function clearChatHistory(): Promise<{ ok: boolean; deleted: number }> {
  const res = await api.delete("/chat/history");
  return res.data;
}

export async function listChats(): Promise<ChatSession[]> {
  const res = await api.get("/chat");
  return res.data;
}
