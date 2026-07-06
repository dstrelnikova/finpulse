import React, { Suspense, useEffect, useMemo, useState } from "react";
import { getNewsFeed, NewsItem } from "../api/news";
import SeoHead from "../components/SeoHead";
import { getApiErrorStatus } from "../api/errors";

const NewsCard = React.lazy(() => import("../components/NewsCard"));

function formatAsof(asof: string | null) {
  if (!asof) return "";
  // asof приходит как "YYYY-MM-DD"
  const [y, m, d] = asof.split("-").map(Number);
  const dt = new Date(y, (m ?? 1) - 1, d ?? 1);
  return dt.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export default function News() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadNews = async () => {
      try {
        setLoading(true);
        setErrorMsg(null);

        const items = await getNewsFeed();
        setNews(items);
      } catch (err: unknown) {
        console.error("Ошибка загрузки новостей", err);
        const status = getApiErrorStatus(err);

        if (status === 401) {
          setErrorMsg("Сессия истекла, нужно заново войти в аккаунт.");
        } else if (status === 503) {
          setErrorMsg("Сервис анализа временно недоступен (LLM). Попробуй позже.");
        } else {
          setErrorMsg("Не удалось загрузить новости. Попробуй позже.");
        }
      } finally {
        setLoading(false);
      }
    };

    loadNews();
  }, []);

  const asofLabel = useMemo(() => {
    // берём дату из первого блока (все блоки обычно одного дня)
    return news.length ? formatAsof(news[0].asof) : "";
  }, [news]);

  return (
    <>
      <SeoHead
        title="Персональная лента | FinPulse"
        description="Личная аналитическая лента новостей по вашему инвестиционному профилю."
        canonicalPath="/news"
        noindex
      />
      <div className="grid gap-4 md:grid-cols-3">
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm md:col-span-2">
        <div className="border-b border-slate-100 bg-slate-950 px-4 py-5 text-white sm:px-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">Персональная лента</p>
            <h1 className="mt-1 text-xl font-semibold sm:text-2xl">Новости по профилю</h1>
            {asofLabel && <p className="mt-1 text-xs text-slate-300">Обзор на {asofLabel}</p>}
          </div>
        </div>

        <div className="p-4 sm:p-5">
        {loading && <p className="text-sm text-gray-500">Загружаю новости…</p>}

        {errorMsg && <p className="text-sm text-red-500 mb-3">{errorMsg}</p>}

        {!loading && !errorMsg && news.length === 0 && (
          <p className="text-sm text-gray-500">
            Пока нет новостей по твоим предпочтениям.
          </p>
        )}

          <div className="space-y-4">
            <Suspense fallback={<p className="text-sm text-gray-500">Подгружаю карточки...</p>}>
              {news.map((item) => (
                <NewsCard key={item.url} item={item} />
              ))}
            </Suspense>
          </div>
          </div>
        </section>

        <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="font-semibold text-slate-950">Подсказка</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Лента формируется по твоему профилю: горизонт, риск, интересующие сектора/акции.
          </p>

          <div className="mt-4 space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
              <span>Позитивно: может поддержать цены/настроения</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-gray-400" />
              <span>Нейтрально: без явного эффекта</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
              <span>Негативно: риск давления на рынок/акции</span>
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}
