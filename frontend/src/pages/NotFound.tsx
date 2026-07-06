import { Link } from "react-router-dom";
import SeoHead from "../components/SeoHead";

export default function NotFound() {
  return (
    <>
      <SeoHead
        title="404 — Страница не найдена | FinPulse"
        description="Запрошенная страница не найдена."
        canonicalPath="/404"
        noindex
      />
      <section className="mx-auto max-w-xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="bg-slate-950 px-6 py-5 text-white">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">FinPulse</p>
          <h1 className="mt-1 text-2xl font-semibold">404</h1>
        </div>
        <div className="space-y-4 p-6">
        <p className="text-sm text-slate-600">Страница не найдена или была перемещена.</p>
        <Link to="/" className="inline-flex h-10 items-center rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800">
          Вернуться на главную
        </Link>
        </div>
      </section>
    </>
  );
}
