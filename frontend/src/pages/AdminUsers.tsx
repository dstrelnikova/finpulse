import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listUsers, setUserRoles, AdminUserRow } from "../api/adminUsers";
import SeoHead from "../components/SeoHead";
import { getApiErrorMessage } from "../api/errors";

const ROLE_OPTIONS = ["", "user", "pro", "admin"] as const;
const ROLE_LABELS: Record<string, string> = {
  user: "Пользователь",
  pro: "Pro",
  admin: "Администратор",
};
const PAGE_SIZES = [5, 20, 50, 100];

type SortBy = "created_at" | "email" | "role";
type SortDir = "asc" | "desc";

function toInt(value: string | null, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(1, Math.floor(parsed)) : fallback;
}

export default function AdminUsers() {
  const [sp, setSp] = useSearchParams();

  const q = sp.get("q") ?? "";
  const role = sp.get("role") ?? "";
  const sort_by = (sp.get("sort_by") as SortBy) ?? "created_at";
  const sort_dir = (sp.get("sort_dir") as SortDir) ?? "desc";
  const page = toInt(sp.get("page"), 1);
  const page_size_raw = Number(sp.get("page_size"));
  const page_size = Number.isFinite(page_size_raw)
    ? Math.min(100, Math.max(5, Math.floor(page_size_raw)))
    : 5;

  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [qDraft, setQDraft] = useState(q);

  useEffect(() => setQDraft(q), [q]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / page_size)), [total, page_size]);
  const adminCount = rows.filter((user) => user.roles.includes("admin")).length;
  const proCount = rows.filter((user) => user.roles.includes("pro")).length;

  const updateParams = useCallback((mutator: (next: URLSearchParams) => void) => {
    const next = new URLSearchParams(sp);
    mutator(next);
    setSp(next, { replace: true });
  }, [setSp, sp]);

  const setParam = useCallback((key: string, value?: string) => {
    updateParams((next) => {
      if (value && value.length) next.set(key, value);
      else next.delete(key);
    });
  }, [updateParams]);

  const setParamResetPage = useCallback((key: string, value?: string) => {
    updateParams((next) => {
      if (value && value.length) next.set(key, value);
      else next.delete(key);
      next.set("page", "1");
    });
  }, [updateParams]);

  function setSort(nextBy: SortBy) {
    updateParams((next) => {
      const currentBy = (sp.get("sort_by") as SortBy) ?? "created_at";
      const currentDir = (sp.get("sort_dir") as SortDir) ?? "desc";
      const nextDir: SortDir = currentBy === nextBy && currentDir === "desc" ? "asc" : "desc";
      next.set("sort_by", nextBy);
      next.set("sort_dir", nextDir);
      next.set("page", "1");
    });
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (qDraft !== q) {
        setParamResetPage("q", qDraft.trim() || undefined);
      }
    }, 350);

    return () => window.clearTimeout(timer);
  }, [q, qDraft, setParamResetPage]);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await listUsers({
        q: q.trim() || undefined,
        role: role || undefined,
        sort_by,
        sort_dir,
        page,
        page_size,
      });

      setRows(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Не удалось загрузить пользователей"));
    } finally {
      setLoading(false);
    }
  }, [page, page_size, q, role, sort_by, sort_dir]);

  useEffect(() => {
    void load();
  }, [load]);

  async function changeRole(userId: number, nextRole: string) {
    if (!nextRole) return;

    setSavingId(userId);
    setError(null);
    try {
      await setUserRoles(userId, [nextRole]);
      await load();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Не удалось изменить роль"));
    } finally {
      setSavingId(null);
    }
  }

  return (
    <>
      <SeoHead
        title="Пользователи | FinPulse"
        description="Служебный раздел администрирования пользователей."
        canonicalPath="/admin/users"
        noindex
      />

      <div className="space-y-6">
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="bg-slate-950 px-5 py-5 text-white sm:px-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-200">
                Администрирование
              </p>
              <h1 className="mt-1 text-2xl font-semibold">Пользователи FinPulse</h1>
              <p className="mt-1 text-sm text-slate-300">
                Роли, доступы и базовая информация по аккаунтам.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Metric label="Всего" value={String(total)} />
              <Metric label="Admin" value={String(adminCount)} />
              <Metric label="Pro" value={String(proCount)} />
            </div>
          </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
              <div className="grid flex-1 grid-cols-1 gap-3 md:grid-cols-[minmax(220px,1fr)_220px_160px]">
                <Field label="Поиск">
                  <input
                    className="h-11 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    value={qDraft}
                    onChange={(event) => setQDraft(event.target.value)}
                    placeholder="email или имя"
                  />
                </Field>

                <Field label="Роль">
                  <select
                    className="h-11 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    value={role}
                    onChange={(event) => setParamResetPage("role", event.target.value || undefined)}
                  >
                    {ROLE_OPTIONS.map((option) => (
                      <option key={option || "all"} value={option}>
                        {option ? ROLE_LABELS[option] ?? option : "Все роли"}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="На странице">
                  <select
                    className="h-11 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    value={page_size}
                    onChange={(event) => {
                      updateParams((next) => {
                        next.set("page_size", String(Number(event.target.value)));
                        next.set("page", "1");
                      });
                    }}
                  >
                    {PAGE_SIZES.map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  className="h-11 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-slate-50"
                  onClick={() => setSp(new URLSearchParams(), { replace: true })}
                >
                  Сбросить
                </button>
                <button
                  type="button"
                  onClick={() => void load()}
                  className="h-11 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                  disabled={loading}
                >
                  {loading ? "Обновляем..." : "Обновить"}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="mx-5 mt-4 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 sm:mx-6">
              {error}
            </div>
          )}

          <div className="px-5 py-5 sm:px-6">
            {loading ? (
              <div className="rounded-md border border-slate-100 bg-slate-50 px-4 py-6 text-sm text-slate-500">
                Загружаем пользователей...
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <SortableHeader active={sort_by === "email"} dir={sort_dir} onClick={() => setSort("email")}>
                        Пользователь
                      </SortableHeader>
                      <SortableHeader active={sort_by === "role"} dir={sort_dir} onClick={() => setSort("role")}>
                        Роль
                      </SortableHeader>
                      <th className="px-3 py-3">Тариф</th>
                      <SortableHeader
                        active={sort_by === "created_at"}
                        dir={sort_dir}
                        onClick={() => setSort("created_at")}
                      >
                        Регистрация
                      </SortableHeader>
                      <th className="px-3 py-3 text-right">ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((user) => {
                      const currentRole = user.roles[0] ?? "user";
                      const isSaving = savingId === user.id;

                      return (
                        <tr key={user.id} className="border-b border-slate-100 transition hover:bg-slate-50/70 last:border-0">
                          <td className="px-3 py-4">
                            <div className="flex items-center gap-3">
                              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-blue-100 bg-blue-50 text-sm font-bold text-blue-700">
                                {getInitials(user.name || user.email)}
                              </div>
                              <div>
                                <p className="font-semibold text-slate-950">{user.email}</p>
                                {user.name && <p className="text-xs text-slate-500">{user.name}</p>}
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-4">
                            <div className="flex items-center gap-2">
                              <select
                                className="h-10 rounded-md border border-slate-200 px-3 text-sm font-medium outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50 disabled:text-slate-400"
                                value={currentRole}
                                disabled={isSaving}
                                onChange={(event) => void changeRole(user.id, event.target.value)}
                              >
                                {ROLE_OPTIONS.filter(Boolean).map((option) => (
                                  <option key={option} value={option}>
                                    {ROLE_LABELS[option] ?? option}
                                  </option>
                                ))}
                              </select>
                              {isSaving && <span className="text-xs font-medium text-blue-600">Сохраняем</span>}
                            </div>
                          </td>
                          <td className="px-3 py-4">
                            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                              {user.subscription_tier || "Базовый"}
                            </span>
                          </td>
                          <td className="px-3 py-4 text-slate-600">{formatDate(user.created_at)}</td>
                          <td className="px-3 py-4 text-right font-mono text-xs text-slate-500">{user.id}</td>
                        </tr>
                      );
                    })}
                    {rows.length === 0 && (
                      <tr>
                        <td className="px-3 py-8 text-center text-sm text-slate-500" colSpan={5}>
                          Пользователи не найдены
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3 border-t border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <p className="text-sm text-slate-500">
              Страница {page} из {totalPages} · всего {total}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="h-10 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
                disabled={page <= 1}
                onClick={() => setParam("page", String(page - 1))}
              >
                Назад
              </button>
              <button
                type="button"
                className="h-10 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
                disabled={page >= totalPages}
                onClick={() => setParam("page", String(page + 1))}
              >
                Вперед
              </button>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold text-slate-700">{label}</span>
      {children}
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-24 rounded-md border border-white/10 bg-white/10 px-3 py-2">
      <p className="text-xs font-medium text-slate-300">{label}</p>
      <p className="mt-1 text-lg font-semibold leading-none text-white">{value}</p>
    </div>
  );
}

function SortableHeader({
  active,
  dir,
  onClick,
  children,
}: {
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <th className="px-3 py-3">
      <button
        type="button"
        className={`inline-flex items-center gap-1 text-left transition hover:text-blue-700 ${
          active ? "text-blue-700" : ""
        }`}
        onClick={onClick}
      >
        {children}
        <span className="text-xs">{active ? (dir === "asc" ? "↑" : "↓") : "↕"}</span>
      </button>
    </th>
  );
}

function getInitials(value: string) {
  const clean = value.trim();
  if (!clean) return "FP";
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return clean.slice(0, 2).toUpperCase();
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
