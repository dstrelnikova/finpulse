import { useEffect, useMemo, useRef, useState } from "react";

import SeoHead from "../components/SeoHead";
import { getImoexQuotes, type MoexQuote } from "../api/moex";

function fmt(v: number | null, digits = 2) {
  if (v === null || Number.isNaN(v)) return "—";
  return v.toLocaleString("ru-RU", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

type MarketAnalyticsTone = "growth" | "decline" | "mixed";

function quoteTone(q: MoexQuote) {
  const value = q.change_percent ?? q.change ?? 0;
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function signedPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) return "—";
  return `${value > 0 ? "+" : ""}${fmt(value)}%`;
}

export default function MoexMarket() {
  const [items, setItems] = useState<MoexQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fallback, setFallback] = useState(false);
  const [fetchedAt, setFetchedAt] = useState<string>("");
  const [highlightedTicker, setHighlightedTicker] = useState<string | null>(null);
  const mobileQuoteRefs = useRef<Record<string, HTMLElement | null>>({});
  const desktopQuoteRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setErrorMsg(null);
        const data = await getImoexQuotes(12);
        setItems(data.items);
        setFallback(data.fallback);
        setFetchedAt(data.fetched_at);
      } catch (err) {
        console.error(err);
        setErrorMsg("Не удалось загрузить котировки MOEX.");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const updatedLabel = useMemo(() => {
    if (!fetchedAt) return "—";
    return new Date(fetchedAt).toLocaleString("ru-RU");
  }, [fetchedAt]);

  const analytics = useMemo(() => {
    if (items.length === 0) return null;

    const growing = items.filter((item) => item.change_percent !== null && item.change_percent > 0);
    const declining = items.filter((item) => item.change_percent !== null && item.change_percent < 0);
    const neutralCount = items.length - growing.length - declining.length;

    const growthShare = growing.length / items.length;
    const declineShare = declining.length / items.length;

    let tone: MarketAnalyticsTone = "mixed";
    let title = "Динамика смешанная";
    let interpretation =
      "В выборке IMOEX нет единого направления: часть бумаг растет, часть находится под давлением.";

    if (growthShare >= 0.6) {
      tone = "growth";
      title = "Преобладает рост";
      interpretation =
        "В выборке IMOEX преобладает положительная динамика: большинство отслеживаемых бумаг торгуется в плюсе.";
    } else if (declineShare >= 0.6) {
      tone = "decline";
      title = "Преобладает снижение";
      interpretation =
        "В выборке IMOEX преобладает давление: большинство отслеживаемых бумаг торгуется в минусе.";
    }

    const leaderGrowth = growing.reduce<MoexQuote | null>((best, item) => {
      if (!best) return item;
      return (item.change_percent ?? 0) > (best.change_percent ?? 0) ? item : best;
    }, null);

    const leaderDecline = declining.reduce<MoexQuote | null>((worst, item) => {
      if (!worst) return item;
      return (item.change_percent ?? 0) < (worst.change_percent ?? 0) ? item : worst;
    }, null);

    return {
      tone,
      title,
      interpretation,
      growingCount: growing.length,
      decliningCount: declining.length,
      neutralCount,
      leaderGrowth,
      leaderDecline,
    };
  }, [items]);

  const analyticsToneClass = analytics
    ? {
        growth: "border-green-200 bg-green-50 text-green-700",
        decline: "border-red-200 bg-red-50 text-red-700",
        mixed: "border-blue-200 bg-blue-50 text-blue-700",
      }[analytics.tone]
    : "";

  const scrollToQuote = (ticker: string | null | undefined) => {
    if (!ticker) return;

    const isDesktop = window.matchMedia("(min-width: 768px)").matches;
    const target = (isDesktop ? desktopQuoteRefs : mobileQuoteRefs).current[ticker];
    if (!target) return;

    setHighlightedTicker(ticker);
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      setHighlightedTicker((current) => (current === ticker ? null : current));
    }, 1600);
  };

  return (
    <>
      <SeoHead
        title="Котировки IMOEX | FinPulse"
        description="Публичная страница котировок акций из корзины индекса Московской биржи (IMOEX)."
        canonicalPath="/market/moex"
      />
      <section className="mx-auto max-w-6xl space-y-4">
        <header className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">MOEX</p>
              <h1 className="mt-1 text-2xl font-semibold text-slate-950">Котировки IMOEX</h1>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">
                Акции из базового набора индекса МосБиржи.
              </p>
            </div>
            <div className="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              <p className="text-xs font-medium uppercase text-slate-400">Обновлено</p>
              <p className="mt-0.5 font-semibold text-slate-800">{updatedLabel}</p>
            </div>
          </div>
        </header>

        {fallback && (
          <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
            Внешний API MOEX временно недоступен, показан fallback-список тикеров без цен.
          </p>
        )}

        {loading && <p className="text-sm text-gray-500">Загрузка котировок...</p>}
        {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}

        {!loading && !errorMsg && analytics && (
          <section className={`rounded-lg border p-4 shadow-sm ${analyticsToneClass}`}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium opacity-80">Аналитика котировок</p>
                <h2 className="text-xl font-semibold mt-1">{analytics.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-gray-700">{analytics.interpretation}</p>
              </div>
              <div className="grid grid-cols-3 gap-2 sm:min-w-64">
                <MiniStat label="Рост" value={analytics.growingCount} tone="positive" />
                <MiniStat label="Минус" value={analytics.decliningCount} tone="negative" />
                <MiniStat label="Нейтр." value={analytics.neutralCount} tone="neutral" />
              </div>
            </div>

            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => scrollToQuote(analytics.leaderGrowth?.ticker)}
                disabled={!analytics.leaderGrowth}
                className="rounded border border-white/70 bg-white/70 p-3 text-left transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                <p className="text-xs text-gray-500">Лидер роста</p>
                {analytics.leaderGrowth ? (
                  <p className="mt-1 font-semibold text-green-700">
                    {analytics.leaderGrowth.ticker} {signedPercent(analytics.leaderGrowth.change_percent)}
                  </p>
                ) : (
                  <p className="mt-1 font-semibold text-gray-600">—</p>
                )}
              </button>
              <button
                type="button"
                onClick={() => scrollToQuote(analytics.leaderDecline?.ticker)}
                disabled={!analytics.leaderDecline}
                className="rounded border border-white/70 bg-white/70 p-3 text-left transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                <p className="text-xs text-gray-500">Лидер снижения</p>
                {analytics.leaderDecline ? (
                  <p className="mt-1 font-semibold text-red-700">
                    {analytics.leaderDecline.ticker} {signedPercent(analytics.leaderDecline.change_percent)}
                  </p>
                ) : (
                  <p className="mt-1 font-semibold text-gray-600">—</p>
                )}
              </button>
            </div>
          </section>
        )}

        {!loading && !errorMsg && (
          <>
            <div className="grid gap-3 md:hidden">
              {items.map((q) => (
                <QuoteCard
                  key={q.ticker}
                  quote={q}
                  highlighted={highlightedTicker === q.ticker}
                  setRef={(node) => {
                    mobileQuoteRefs.current[q.ticker] = node;
                  }}
                />
              ))}
            </div>

            <DesktopQuotesTable
              items={items}
              highlightedTicker={highlightedTicker}
              setQuoteRef={(ticker, node) => {
                desktopQuoteRefs.current[ticker] = node;
              }}
            />
          </>
        )}
      </section>
    </>
  );
}

function DesktopQuotesTable({
  items,
  highlightedTicker,
  setQuoteRef,
}: {
  items: MoexQuote[];
  highlightedTicker: string | null;
  setQuoteRef: (ticker: string, node: HTMLTableRowElement | null) => void;
}) {
  return (
    <section className="hidden overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm md:block">
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-950 px-5 py-4 text-white">
        <div>
          <h2 className="text-base font-semibold">Список бумаг</h2>
          <p className="mt-0.5 text-xs text-slate-300">Цена, дневное изменение и время последней сделки</p>
        </div>
        <div className="rounded-md border border-white/10 bg-white/10 px-3 py-1.5 text-sm font-semibold">
          {items.length} тикеров
        </div>
      </div>

      <div className="max-h-[620px] overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50/95 backdrop-blur">
            <tr className="text-left text-[11px] font-semibold uppercase text-slate-500">
              <th className="px-5 py-3">Инструмент</th>
              <th className="px-4 py-3 text-right">Последняя цена</th>
              <th className="px-4 py-3 text-right">Изменение</th>
              <th className="px-4 py-3 text-right">Динамика</th>
              <th className="px-5 py-3 text-right">Время</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((quote) => {
              const tone = quoteTone(quote);
              const isHighlighted = highlightedTicker === quote.ticker;
              const rowToneClass = {
                positive: "hover:bg-green-50/60",
                negative: "hover:bg-red-50/60",
                neutral: "hover:bg-slate-50",
              }[tone];

              return (
                <tr
                  key={quote.ticker}
                  ref={(node) => setQuoteRef(quote.ticker, node)}
                  className={`transition ${rowToneClass} ${
                    isHighlighted ? "bg-blue-50 ring-2 ring-inset ring-blue-200" : "bg-white"
                  }`}
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-sm font-bold text-slate-950">
                        {quote.ticker.slice(0, 2)}
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-slate-950">{quote.ticker}</p>
                        <p className="mt-0.5 max-w-[360px] truncate text-xs text-slate-500">
                          {quote.short_name || "Название не указано"}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <p className="font-semibold tabular-nums text-slate-950">{fmt(quote.last)}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{quote.currency}</p>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <ChangeValue value={quote.change} tone={tone} />
                  </td>
                  <td className="px-4 py-4 text-right">
                    <ChangeBadge value={quote.change_percent} tone={tone} />
                  </td>
                  <td className="px-5 py-4 text-right text-xs font-medium text-slate-500">
                    {quote.update_time || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChangeValue({ value, tone }: { value: number | null; tone: ReturnType<typeof quoteTone> }) {
  const toneClass = {
    positive: "text-green-700",
    negative: "text-red-700",
    neutral: "text-slate-600",
  }[tone];

  return <span className={`font-semibold tabular-nums ${toneClass}`}>{value && value > 0 ? "+" : ""}{fmt(value)}</span>;
}

function ChangeBadge({ value, tone }: { value: number | null; tone: ReturnType<typeof quoteTone> }) {
  const toneClass = {
    positive: "border-green-200 bg-green-50 text-green-700",
    negative: "border-red-200 bg-red-50 text-red-700",
    neutral: "border-slate-200 bg-slate-50 text-slate-600",
  }[tone];

  return (
    <span className={`inline-flex min-w-20 justify-center rounded-full border px-2.5 py-1 text-xs font-bold tabular-nums ${toneClass}`}>
      {signedPercent(value)}
    </span>
  );
}

function MiniStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "positive" | "negative" | "neutral";
}) {
  const toneClass = {
    positive: "text-green-700",
    negative: "text-red-700",
    neutral: "text-slate-700",
  }[tone];

  return (
    <div className="rounded-md border border-white/70 bg-white/70 p-2 text-center">
      <p className="text-[11px] font-medium text-slate-500">{label}</p>
      <p className={`mt-0.5 text-xl font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

function QuoteCard({
  quote,
  highlighted = false,
  setRef,
}: {
  quote: MoexQuote;
  highlighted?: boolean;
  setRef?: (node: HTMLElement | null) => void;
}) {
  const tone = quoteTone(quote);
  const toneClass = {
    positive: "border-green-100 bg-green-50 text-green-700",
    negative: "border-red-100 bg-red-50 text-red-700",
    neutral: "border-slate-100 bg-slate-50 text-slate-600",
  }[tone];
  const valueClass = {
    positive: "text-green-700",
    negative: "text-red-700",
    neutral: "text-slate-600",
  }[tone];
  const highlightClass = highlighted ? "border-blue-300 bg-blue-50/70 ring-2 ring-blue-200" : "border-slate-200 bg-white";

  return (
    <article ref={setRef} className={`rounded-lg border p-4 shadow-sm transition ${highlightClass}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-slate-950">{quote.ticker}</h2>
            <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${toneClass}`}>
              {signedPercent(quote.change_percent)}
            </span>
          </div>
          <p className="mt-1 truncate text-sm text-slate-500">{quote.short_name || "Название не указано"}</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-slate-950">{fmt(quote.last)}</p>
          <p className="text-xs font-medium text-slate-400">{quote.currency}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <div className="rounded-md bg-slate-50 p-2">
          <p className="text-[11px] font-medium uppercase text-slate-400">Изменение</p>
          <p className={`mt-0.5 text-sm font-semibold ${valueClass}`}>{fmt(quote.change)}</p>
        </div>
        <div className="rounded-md bg-slate-50 p-2">
          <p className="text-[11px] font-medium uppercase text-slate-400">Время</p>
          <p className="mt-0.5 text-sm font-semibold text-slate-700">{quote.update_time || "—"}</p>
        </div>
      </div>
    </article>
  );
}
