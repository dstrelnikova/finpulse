import React, { Suspense, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SeoHead from "../components/SeoHead";
import { getPublicNewsItemBySlug, NewsItem } from "../api/news";
import { getApiErrorStatus } from "../api/errors";

const NewsCard = React.lazy(() => import("../components/NewsCard"));
const SITE_URL = import.meta.env.VITE_SITE_URL ?? "http://localhost:3000";

export default function PublicNewsItem() {
  const { slug } = useParams<{ slug: string }>();
  const [item, setItem] = useState<NewsItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!slug) return;
      try {
        setLoading(true);
        setErrorMsg(null);
        const data = await getPublicNewsItemBySlug(slug);
        setItem(data);
      } catch (err: unknown) {
        console.error("Ошибка загрузки публичной новости", err);
        setErrorMsg(getApiErrorStatus(err) === 404 ? "Новость не найдена." : "Ошибка загрузки новости.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [slug]);

  const structuredData = useMemo(() => {
    if (!item) return undefined;
    return {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      headline: item.title,
      datePublished: item.asof ?? undefined,
      articleBody: item.summary,
      mainEntityOfPage: `${SITE_URL}/news/public/${item.slug}`,
      publisher: {
        "@type": "Organization",
        name: "FinPulse",
      },
    };
  }, [item]);

  return (
    <>
      <SeoHead
        title={item ? `${item.title} | FinPulse` : "Новость | FinPulse"}
        description={item?.summary || "Аналитическая карточка новости российского фондового рынка."}
        canonicalPath={`/news/public/${slug ?? ""}`}
        type="article"
        structuredData={structuredData}
      />

      <section className="mx-auto max-w-4xl space-y-4">
        <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
          <Link
            to="/news/public"
            className="inline-flex h-9 items-center rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            ← Вернуться к ленте
          </Link>
        </div>

        {loading && (
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
            Загружаю новость...
          </div>
        )}
        {errorMsg && (
          <div className="rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700">
            {errorMsg}
          </div>
        )}

        {!loading && !errorMsg && item && (
          <Suspense fallback={<p className="text-sm text-gray-500">Подгружаю карточку...</p>}>
            <NewsCard item={item} />
          </Suspense>
        )}
      </section>
    </>
  );
}
