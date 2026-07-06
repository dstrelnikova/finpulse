import { Suspense, useEffect, useMemo, useState } from "react";
import SeoHead from "../components/SeoHead";
import { getPublicNewsFeed, type Confidence, type Impact, type NewsItem } from "../api/news";
import { getApiErrorStatus } from "../api/errors";

import { lazy } from "react";

const NewsCard = lazy(() => import("../components/NewsCard"));
const SITE_URL = import.meta.env.VITE_SITE_URL ?? "http://localhost:3000";

const CACHE_TTL_MS = 5 * 60 * 1000;
let cachedFeed: { at: number; items: NewsItem[] } | null = null;

type ImpactFilter = "all" | Impact;
type SortMode = "important" | "new";

const FILTERS: { value: ImpactFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "positive", label: "Позитив" },
  { value: "neutral", label: "Нейтрал" },
  { value: "negative", label: "Негатив" },
];

const SORT_MODES: { value: SortMode; label: string }[] = [
  { value: "important", label: "Сначала важные" },
  { value: "new", label: "Сначала новые" },
];

const CONF_WEIGHT: Record<Confidence, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

const IMPACT_WEIGHT: Record<Impact, number> = {
  negative: 2,
  positive: 2,
  neutral: 1,
};

export default function PublicNews() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<ImpactFilter>("all");
  const [sortMode, setSortMode] = useState<SortMode>("important");
  const [lastLoadedAt, setLastLoadedAt] = useState<number | null>(null);

  const loadNews = async (ignoreCache = false) => {
    try {
      setLoading(true);
      setErrorMsg(null);

      if (!ignoreCache && cachedFeed && Date.now() - cachedFeed.at < CACHE_TTL_MS) {
        setNews(cachedFeed.items);
        setLastLoadedAt(cachedFeed.at);
        return;
      }

      const items = await getPublicNewsFeed(50);
      const loadedAt = Date.now();
      cachedFeed = { at: loadedAt, items };
      setNews(items);
      setLastLoadedAt(loadedAt);
    } catch (err: unknown) {
      console.error("Ошибка загрузки публичных новостей", err);
      if (getApiErrorStatus(err) === 503) {
        setErrorMsg("Внешний источник временно недоступен. Показываем ленту позже.");
      } else {
        setErrorMsg("Не удалось загрузить новости.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadNews();
  }, []);

  const stats = useMemo(() => {
    const positive = news.filter((item) => item.indicator?.impact === "positive").length;
    const negative = news.filter((item) => item.indicator?.impact === "negative").length;
    const neutral = news.filter((item) => item.indicator?.impact === "neutral" || !item.indicator).length;
    const highConfidence = news.filter((item) => item.indicator?.confidence === "high").length;
    return { positive, negative, neutral, highConfidence };
  }, [news]);

  const filteredNews = useMemo(() => {
    const filtered = activeFilter === "all" ? news : news.filter((item) => item.indicator?.impact === activeFilter);
    if (sortMode === "new") return filtered;

    return filtered
      .map((item, index) => ({ item, index }))
      .sort((a, b) => {
        const aConfidence = a.item.indicator ? CONF_WEIGHT[a.item.indicator.confidence] : 0;
        const bConfidence = b.item.indicator ? CONF_WEIGHT[b.item.indicator.confidence] : 0;
        if (aConfidence !== bConfidence) return bConfidence - aConfidence;

        const aImpact = a.item.indicator ? IMPACT_WEIGHT[a.item.indicator.impact] : 0;
        const bImpact = b.item.indicator ? IMPACT_WEIGHT[b.item.indicator.impact] : 0;
        if (aImpact !== bImpact) return bImpact - aImpact;

        return a.index - b.index;
      })
      .map(({ item }) => item);
  }, [activeFilter, news, sortMode]);

  const filterCounts = useMemo<Record<ImpactFilter, number>>(
    () => ({
      all: news.length,
      positive: stats.positive,
      neutral: stats.neutral,
      negative: stats.negative,
    }),
    [news.length, stats.negative, stats.neutral, stats.positive]
  );

  const loadedLabel = useMemo(() => {
    if (!lastLoadedAt) return "";
    return new Date(lastLoadedAt).toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [lastLoadedAt]);

  const structuredData = useMemo(() => {
    const top = news.slice(0, 5);
    return {
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      name: "Публичная лента новостей FinPulse",
      description: "Ключевые новости российского фондового рынка с краткой аналитикой.",
      mainEntity: top.map((item) => ({
        "@type": "NewsArticle",
        headline: item.title,
        datePublished: item.asof ?? undefined,
        url: `${SITE_URL}/news/public/${item.slug}`,
        publisher: { "@type": "Organization", name: "FinPulse" },
      })),
    };
  }, [news]);

  return (
    <>
      <SeoHead
        title="Публичные новости рынка РФ | FinPulse"
        description="Публичная лента ключевых новостей российского фондового рынка с краткими выводами и рисками."
        canonicalPath="/news/public"
        type="website"
        structuredData={structuredData}
      />

      <section className="space-y-4">
        <header className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 bg-slate-950 px-4 py-5 text-white sm:px-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">FinPulse News</p>
                <h1 className="mt-1 text-2xl font-semibold">Публичная лента новостей</h1>
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300">
                  Короткая выжимка по рынку РФ: факты, влияние и риски без лишнего шума.
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
                  <span className="rounded border border-white/10 bg-white/10 px-2 py-1">Материалы за 7 дней</span>
                  {loadedLabel && (
                    <span className="rounded border border-white/10 bg-white/10 px-2 py-1">
                      Обновлено: {loadedLabel}
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => void loadNews(true)}
                disabled={loading}
                className="self-start rounded-md border border-white/15 bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Обновляю..." : "Обновить"}
              </button>
            </div>
          </div>

          {!loading && !errorMsg && news.length > 0 && (
            <div className="grid gap-0 divide-y divide-slate-100 sm:grid-cols-[1.3fr_1fr] sm:divide-x sm:divide-y-0">
              <div className="px-4 py-4 sm:px-6">
                <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Сводка</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  В ленте {news.length} материалов. Важные новости подняты выше, а цвет сигнала показывает вероятное
                  влияние на рынок или сектор.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 px-4 py-4 sm:px-6">
                <FeedStat label="Материалов" value={news.length} className="text-slate-950" />
                <FeedStat label="Высокая уверенность" value={stats.highConfidence} className="text-blue-700" />
              </div>
            </div>
          )}
        </header>

        {!loading && !errorMsg && news.length > 0 && (
          <section className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex gap-2 overflow-x-auto pb-1 lg:pb-0">
                {SORT_MODES.map((mode) => (
                  <button
                    key={mode.value}
                    type="button"
                    onClick={() => setSortMode(mode.value)}
                    className={
                      "h-9 whitespace-nowrap rounded-md border px-3 text-sm font-semibold transition " +
                      (sortMode === mode.value
                        ? "border-gray-900 bg-gray-900 text-white"
                        : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50")
                    }
                  >
                    {mode.label}
                  </button>
                ))}
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1 lg:pb-0">
                {FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => setActiveFilter(filter.value)}
                    className={
                      "h-9 whitespace-nowrap rounded-md border px-3 text-sm font-semibold transition " +
                      (activeFilter === filter.value
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50")
                    }
                  >
                    {filter.label} {filterCounts[filter.value]}
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}

        <section className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
          {loading && <NewsLoading />}
          {errorMsg && <p className="text-sm text-red-500">{errorMsg}</p>}
          {!loading && !errorMsg && news.length === 0 && (
            <p className="text-sm text-gray-500">Пока нет опубликованных материалов.</p>
          )}

          <div className="space-y-3">
            <Suspense fallback={<p className="text-sm text-gray-500">Подгружаю карточки...</p>}>
              {filteredNews.map((item) => (
                <NewsCard key={String(item.id)} item={item} />
              ))}
            </Suspense>
          </div>

          {!loading && !errorMsg && news.length > 0 && filteredNews.length === 0 && (
            <p className="mt-4 rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
              По выбранному фильтру пока нет новостей.
            </p>
          )}
        </section>
      </section>
    </>
  );
}

function FeedStat({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div className="rounded-md border border-slate-100 bg-slate-50 p-2 text-center">
      <p className="text-[11px] font-semibold text-slate-500">{label}</p>
      <p className={`mt-0.5 text-xl font-semibold ${className}`}>{value}</p>
    </div>
  );
}

function NewsLoading() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((item) => (
        <div key={item} className="animate-pulse rounded-lg border border-slate-100 bg-slate-50 p-4">
          <div className="h-3 w-32 rounded bg-slate-200" />
          <div className="mt-3 h-5 w-3/4 rounded bg-slate-200" />
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="h-24 rounded bg-slate-200/70" />
            <div className="h-24 rounded bg-slate-200/70" />
          </div>
        </div>
      ))}
    </div>
  );
}
