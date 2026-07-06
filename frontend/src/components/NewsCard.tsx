import type { NewsItem, Impact, Confidence } from "../api/news";
import { openExternalUrl } from "../utils/openExternalUrl";

type Props = {
  item: NewsItem;
};

const IMPACT_LABELS: Record<Impact, string> = {
  positive: "Позитив",
  neutral: "Нейтрал",
  negative: "Негатив",
};

const IMPACT_BADGE: Record<Impact, string> = {
  positive: "bg-green-50 text-green-700 border-green-200",
  neutral: "bg-slate-50 text-slate-700 border-slate-200",
  negative: "bg-red-50 text-red-700 border-red-200",
};

const CONF_LABELS: Record<Confidence, string> = {
  low: "низкая",
  medium: "средняя",
  high: "высокая",
};

const CONF_BADGE: Record<Confidence, string> = {
  low: "bg-gray-50 text-gray-700 border-gray-200",
  medium: "bg-blue-50 text-blue-700 border-blue-200",
  high: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

const IMPORTANCE_LABELS: Record<Confidence, string> = {
  low: "низкая важность",
  medium: "средняя важность",
  high: "высокая важность",
};

const GENERIC_RISK_MARKERS = [
  "rss/быстрый анализ",
  "может не учитывать полный текст",
  "сигнал может измениться",
];

const SIGNAL_TEXT: Record<Impact, string> = {
  positive: "Новость скорее поддерживает ожидания по соответствующему сегменту рынка.",
  neutral: "Новость не дает однозначного рыночного сигнала и требует сопоставления с другими событиями.",
  negative: "Новость может усиливать осторожность инвесторов и давление на соответствующий сегмент.",
};

const SIGNAL_TONE: Record<Impact, string> = {
  positive: "border-green-100 bg-green-50 text-green-900",
  neutral: "border-slate-100 bg-slate-50 text-slate-800",
  negative: "border-red-100 bg-red-50 text-red-900",
};

const CARD_ACCENT: Record<Impact, string> = {
  positive: "border-l-green-500",
  neutral: "border-l-slate-300",
  negative: "border-l-red-500",
};

const BLOCK_TITLE_CLASS = "mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500";
const BLOCK_CLASS = "h-full rounded-md border border-slate-100 bg-slate-50 p-3";

function isGenericRisk(value: string) {
  const normalized = value.toLowerCase();
  return GENERIC_RISK_MARKERS.some((marker) => normalized.includes(marker));
}

function cleanDisplayText(value: string) {
  return value
    .replace(/^Новость:\s*/i, "")
    .replace(/'([^']+)'/g, "«$1»")
    .replace(/\s+/g, " ")
    .replace(/\(\s+/g, "(")
    .replace(/\s+\)/g, ")")
    .replace(/\s+([,.:;!?])/g, "$1")
    .replace(/([,.:;!?]){2,}/g, "$1")
    .replace(/[;:,\s]+$/g, "")
    .trim();
}

function formatSentence(value: string) {
  const trimmed = cleanDisplayText(value);
  if (!trimmed) return "";
  const capitalized = trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
  if (/[.!?]$/.test(capitalized) || /[.!?]»$/.test(capitalized)) return capitalized;
  return `${capitalized}.`;
}

function isSimilarText(left: string, right: string) {
  const a = new Set(left.toLowerCase().match(/[а-яёa-z0-9]{4,}/gi) ?? []);
  const b = new Set(right.toLowerCase().match(/[а-яёa-z0-9]{4,}/gi) ?? []);
  if (!a.size || !b.size) return false;
  let hits = 0;
  a.forEach((word) => {
    if (b.has(word)) hits += 1;
  });
  return hits / Math.min(a.size, b.size) >= 0.75;
}

function formatNewsDate(asof: string | null) {
  if (!asof) return "";
  const [datePart] = asof.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  if (!y || !m || !d) return "";
  const dt = new Date(y, m - 1, d);
  return dt.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function NewsCard({ item }: Props) {
  const ind = item.indicator;
  const newsDate = formatNewsDate(item.asof);
  const importance: Confidence = ind?.importance ?? ind?.confidence ?? "low";

  const bullets = (item.bullets ?? [])
    .filter(Boolean)
    .filter((fact) => !/^(Источник|Тема|Материал):/i.test(fact.trim()))
    .filter((fact) => fact.length <= 180)
    .map(formatSentence)
    .slice(0, 3);
  const normalizedSummary = cleanDisplayText(item.summary ?? "");
  const detailFallback =
    normalizedSummary && !isSimilarText(normalizedSummary, item.title)
      ? formatSentence(normalizedSummary)
      : "Источник не содержит достаточно конкретных деталей для расширенного списка фактов.";
  const rationale = (ind?.rationale ?? []).filter(Boolean).map(formatSentence);
  const visibleRationale = rationale.slice(0, 3);
  const risks = (item.risks ?? []).filter(Boolean).filter((risk) => !isGenericRisk(risk)).map(formatSentence);
  const visibleRisks = risks.slice(0, 3);
  const marketMeaningRaw = item.market_meaning || item.conclusion || "";
  const marketMeaning = marketMeaningRaw && !isSimilarText(marketMeaningRaw, item.title)
    ? formatSentence(marketMeaningRaw)
    : ind
      ? SIGNAL_TEXT[ind.impact]
      : "";
  const affectedSegments = (item.affected_segments ?? [])
    .filter(Boolean)
    .map((segment) => cleanDisplayText(segment))
    .filter(Boolean)
    .slice(0, 4);
  const signalClass = ind ? SIGNAL_TONE[ind.impact] : "border-blue-100 bg-blue-50 text-gray-800";
  const accentClass = ind ? CARD_ACCENT[ind.impact] : "border-l-blue-400";

  return (
    <article className={`rounded-lg border border-l-4 border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow-md ${accentClass}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium uppercase text-gray-500">
            <span>{item.source}</span>
            {newsDate && (
              <>
                <span aria-hidden="true" className="text-gray-300">•</span>
                <time dateTime={item.asof ?? undefined}>{newsDate}</time>
              </>
            )}
          </p>
          <h3 className="mt-1 text-lg font-semibold leading-snug text-gray-950 break-words">
            {item.title}
          </h3>
        </div>

        <button
          type="button"
          onClick={() => void openExternalUrl(item.url)}
          disabled={!item.url}
          className="h-9 self-start whitespace-nowrap rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Источник
        </button>
      </div>

      {ind && (
        <div className="mt-3 flex flex-wrap gap-2">
          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${IMPACT_BADGE[ind.impact]}`}
            title="Общее влияние новости на рынок/сектор"
          >
            {IMPACT_LABELS[ind.impact]}
          </span>

          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${CONF_BADGE[ind.confidence]}`}
            title="Насколько уверенно модель оценивает вывод"
          >
            Уверенность: {CONF_LABELS[ind.confidence]}
          </span>

          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${CONF_BADGE[importance]}`}
            title="Насколько это стоит внимания"
          >
            {IMPORTANCE_LABELS[importance]}
          </span>
        </div>
      )}

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {ind && (
          <section className={`order-1 h-full rounded-md border p-3 md:order-2 ${signalClass}`}>
            <p className={BLOCK_TITLE_CLASS}>Рыночный сигнал</p>
            <p className="text-sm leading-relaxed">{marketMeaning}</p>
            {affectedSegments.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {affectedSegments.map((segment) => (
                  <span
                    key={segment}
                    className="rounded border border-current/10 bg-white/50 px-2 py-0.5 text-xs font-medium"
                  >
                    {segment}
                  </span>
                ))}
              </div>
            )}
            <p className="mt-2 text-xs opacity-80">
              Уверенность: {CONF_LABELS[ind.confidence]}. Важность: {IMPORTANCE_LABELS[importance]}.
            </p>
          </section>
        )}

        {bullets.length > 0 && (
          <section className={`${BLOCK_CLASS} order-2 md:order-1`}>
            <p className={BLOCK_TITLE_CLASS}>Ключевые факты</p>
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-gray-700 marker:text-gray-400">
              {bullets.map((b, i) => (
                <li key={i} className="leading-relaxed">
                  {b}
                </li>
              ))}
            </ul>
          </section>
        )}

        {bullets.length === 0 && (
          <section className={`${BLOCK_CLASS} order-2 md:order-1`}>
            <p className={BLOCK_TITLE_CLASS}>Детали</p>
            <p className="text-sm leading-relaxed text-gray-700">{detailFallback}</p>
            <p className="mt-2 text-xs leading-relaxed text-gray-500">
              В анонсе мало проверяемых фактов; подробности лучше сверить в источнике.
            </p>
          </section>
        )}

        {visibleRationale.length > 0 && (
          <section className={`${BLOCK_CLASS} order-3`}>
            <p className={BLOCK_TITLE_CLASS}>Почему такой индикатор</p>
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-gray-700 marker:text-gray-400">
              {visibleRationale.map((r, i) => (
                <li key={i} className="leading-relaxed">
                  {r}
                </li>
              ))}
            </ul>
          </section>
        )}

        {visibleRisks.length > 0 && (
          <section className="order-4 h-full rounded-md border border-red-100 bg-red-50 p-3">
            <p className={BLOCK_TITLE_CLASS}>Главный риск</p>
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-red-800 marker:text-red-300">
              {visibleRisks.map((r, i) => (
                <li key={i} className="leading-relaxed">
                  {r}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </article>
  );
}
