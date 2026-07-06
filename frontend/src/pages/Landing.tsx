import { Link } from 'react-router-dom'
import SeoHead from "../components/SeoHead";

export default function Landing() {
  return (
    <>
      <SeoHead
        title="FinPulse — AI-ассистент для инвестора"
        description="FinPulse помогает быстро понять новости российского фондового рынка и их влияние на инвестиционные решения."
        canonicalPath="/"
      />
      <section className="grid min-h-[calc(100vh-104px)] content-start gap-5 pb-8 md:grid-cols-[1.05fr_0.95fr] md:items-center md:gap-8">
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="bg-slate-950 px-5 py-7 text-white sm:px-6 sm:py-8">
            <div className="mb-5 inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/10 px-3 py-2 text-xs font-semibold uppercase text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Российский рынок
            </div>

            <h1 className="max-w-3xl text-3xl font-bold leading-tight sm:text-5xl">
              FinPulse
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-300 sm:text-lg">
              AI-ассистент, который собирает новости рынка РФ, выделяет главное и объясняет возможное влияние на бумаги, сектор и портфель.
            </p>
          </div>

          <div className="grid gap-3 px-5 py-5 sm:flex sm:px-6">
            <Link
              to="/news/public"
              className="inline-flex h-12 items-center justify-center rounded-md bg-slate-900 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              Открыть ленту
            </Link>
            <Link
              to="/market/moex"
              className="inline-flex h-12 items-center justify-center rounded-md border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
            >
              Котировки MOEX
            </Link>
          </div>
        </div>

        <div className="space-y-3">
          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Сводка</p>
                <h2 className="mt-1 text-lg font-semibold text-slate-950">Что важно сегодня</h2>
              </div>
              <img src="/icon.png" alt="" className="h-11 w-11 rounded-md" />
            </div>
            <div className="mt-4 grid gap-3">
              <div className="rounded-md bg-slate-50 p-3">
                <p className="text-sm font-semibold text-slate-900">Новости</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">Короткая аналитика: факты, вывод, риск и рыночный сигнал.</p>
              </div>
              <div className="rounded-md bg-slate-50 p-3">
                <p className="text-sm font-semibold text-slate-900">MOEX</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">Быстрая проверка индекса, валюты и ликвидных инструментов.</p>
              </div>
              <div className="rounded-md bg-slate-50 p-3">
                <p className="text-sm font-semibold text-slate-900">Чат</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">Вопросы по рынку, портфелю и рискам в одном диалоге.</p>
              </div>
            </div>
          </section>
        </div>
      </section>
    </>
  )
}
