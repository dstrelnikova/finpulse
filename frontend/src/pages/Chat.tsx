import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import Message from "../components/Message";
import SeoHead from "../components/SeoHead";
import { clearChatHistory, getChatHistory, listChats, sendChatMessage } from "../api/chat";
import { getApiErrorDetail } from "../api/errors";

type MessageType = {
  id: number;
  author: string;
  text: string;
  time: string;
  isBot: boolean;
};

export default function Chat() {
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [text, setText] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [loadingChat, setLoadingChat] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const formatTime = (date?: Date) => {
    const d = date ?? new Date();
    return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  };

  useEffect(() => {
    const loadChat = async () => {
      setLoadingChat(true);
      setErrorMsg(null);
      try {
        const chats = await listChats();
        setSelectedChatId(chats[0]?.id ?? null);
      } catch (err) {
        console.error("Ошибка загрузки чата", err);
        setErrorMsg("Не удалось загрузить чат");
      } finally {
        setLoadingChat(false);
      }
    };

    loadChat();
  }, []);

  useEffect(() => {
    const loadHistory = async () => {
      if (!selectedChatId) return;

      setLoadingHistory(true);
      setErrorMsg(null);
      try {
        const history = await getChatHistory(80, selectedChatId);
        setMessages(
          history.map((item) => ({
            id: item.id,
            author: item.role === "FinPulse" ? "FinPulse" : "Пользователь",
            text: item.content,
            time: formatTime(new Date(item.created_at)),
            isBot: item.role === "FinPulse",
          }))
        );
      } catch (err) {
        console.error("Ошибка загрузки истории", err);
        setErrorMsg("Не удалось загрузить историю чата");
        setMessages([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, [selectedChatId]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "auto") => {
    requestAnimationFrame(() => {
      bottomRef.current?.scrollIntoView({ block: "end", behavior });
    });
  }, []);

  useLayoutEffect(() => {
    if (!loadingChat && !loadingHistory) {
      scrollToBottom("auto");
    }
  }, [loadingChat, loadingHistory, selectedChatId, scrollToBottom]);

  useEffect(() => {
    scrollToBottom(messages.length > 1 ? "smooth" : "auto");
  }, [messages.length, isTyping, scrollToBottom]);

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!text.trim() || loading || !selectedChatId) return;

    const userText = text.trim();
    setText("");
    setErrorMsg(null);
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        author: "Пользователь",
        text: userText,
        time: formatTime(),
        isBot: false,
      },
    ]);
    setLoading(true);
    setIsTyping(true);

    try {
      const response = await sendChatMessage({ message: userText, chat_id: selectedChatId });
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          author: "FinPulse",
          text: response.answer,
          time: formatTime(),
          isBot: true,
        },
      ]);
    } catch (err: unknown) {
      console.error("Ошибка отправки сообщения", err);
      const detail = getApiErrorDetail(err);
      setErrorMsg(
        detail === "CHAT_MODEL_UNAVAILABLE"
          ? "Модель чата временно недоступна. Попробуйте ещё раз через минуту."
          : "Не удалось отправить сообщение"
      );
    } finally {
      setIsTyping(false);
      setLoading(false);
    }
  };

  const onConfirmClear = async () => {
    setClearing(true);
    setErrorMsg(null);
    try {
      await clearChatHistory();
      setMessages([]);
      setConfirmClearOpen(false);
    } catch (err) {
      console.error("Ошибка очистки истории", err);
      setErrorMsg("Не удалось очистить историю");
    } finally {
      setClearing(false);
    }
  };

  return (
    <>
      <SeoHead
        title="Чат с AI | FinPulse"
        description="Закрытый раздел личного чата с AI-ассистентом FinPulse."
        canonicalPath="/chat"
        noindex
      />

      <section className="mx-auto flex h-[calc(100vh-104px)] min-h-[520px] max-w-6xl flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm sm:h-[calc(100vh-132px)] sm:min-h-[620px]">
        <header className="border-b border-slate-100 bg-slate-950 px-4 py-3 text-white sm:px-6 sm:py-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">Личный чат</p>
              <h1 className="mt-1 text-xl font-semibold sm:text-2xl">FinPulse</h1>
              <p className="mt-1 text-sm text-slate-300">Вопросы по рынку, рискам и портфелю.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="h-10 rounded-md border border-white/15 bg-white/10 px-4 text-sm font-semibold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:text-slate-500"
                disabled={!selectedChatId || messages.length === 0 || clearing}
                onClick={() => setConfirmClearOpen(true)}
              >
                Очистить историю
              </button>
            </div>
          </div>
        </header>

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-slate-50/70 px-4 py-5 sm:px-6"
          style={{ scrollbarGutter: "stable" }}
        >
          <div className="space-y-4 pb-2">
            {errorMsg && (
              <div className="rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {errorMsg}
              </div>
            )}

            {(loadingChat || loadingHistory) && (
              <div className="rounded-md border border-slate-100 bg-white px-4 py-3 text-sm text-slate-500">
                Загружаю чат...
              </div>
            )}

            {!loadingChat && !loadingHistory && messages.length === 0 && (
              <div className="mx-auto max-w-xl rounded-lg border border-slate-200 bg-white px-5 py-5 text-center shadow-sm">
                <h2 className="text-lg font-semibold text-slate-950">История пуста</h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Напишите вопрос про рынок, портфель, риск или конкретный тикер.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <Message key={message.id} {...message} />
            ))}

            {isTyping && (
              <div className="inline-flex rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-500 shadow-sm">
                FinPulse печатает...
              </div>
            )}
            <div ref={bottomRef} aria-hidden="true" />
          </div>
        </div>

        <form onSubmit={send} className="border-t border-slate-100 bg-white px-4 py-4 sm:px-6">
          <div className="grid gap-2 sm:flex">
            <input
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Спросите про рынок, портфель или риск..."
              className="h-12 min-w-0 flex-1 rounded-md border border-slate-200 px-4 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              disabled={loading || !selectedChatId}
            />

            <button
              type="submit"
              disabled={loading || !text.trim() || !selectedChatId}
              className="h-12 rounded-md bg-slate-900 px-5 text-base font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {loading ? "Отправка..." : "Отправить"}
            </button>
          </div>
        </form>
      </section>

      {confirmClearOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/40 px-4 py-6 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="clear-chat-title"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setConfirmClearOpen(false);
          }}
        >
          <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white shadow-xl">
            <div className="border-b border-gray-100 px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-red-600">Очистка истории</p>
              <h2 id="clear-chat-title" className="mt-1 text-2xl font-semibold text-gray-950">
                Очистить чат?
              </h2>
            </div>
            <div className="px-5 py-5">
              <p className="text-sm leading-relaxed text-gray-600">
                Все сообщения в текущем диалоге будут удалены. Настройки профиля не изменятся.
              </p>
            </div>
            <div className="flex flex-col-reverse gap-2 border-t border-gray-100 px-5 py-4 sm:flex-row sm:justify-end">
              <button
                type="button"
                disabled={clearing}
                className="h-11 rounded-md border border-gray-200 px-4 text-sm font-semibold text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-300"
                onClick={() => setConfirmClearOpen(false)}
              >
                Отмена
              </button>
              <button
                type="button"
                disabled={clearing}
                className="h-11 rounded-md bg-red-600 px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
                onClick={() => void onConfirmClear()}
              >
                {clearing ? "Очищаем..." : "Очистить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
