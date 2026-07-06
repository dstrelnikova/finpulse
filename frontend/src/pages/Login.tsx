import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import SeoHead from "../components/SeoHead";
import { getApiErrorMessage } from "../api/errors";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await loginUser({ email, password });

      await login({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });

      navigate("/profile");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Ошибка входа"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <SeoHead
        title="Вход | FinPulse"
        description="Вход в аккаунт FinPulse для доступа к персональной аналитике."
        canonicalPath="/login"
      />
      <div className="mx-auto max-w-md overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-950 px-5 py-5 text-white sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">Аккаунт</p>
          <h1 className="mt-1 text-2xl font-semibold">Войти</h1>
          <p className="mt-2 text-sm text-slate-300">Доступ к профилю и личному чату FinPulse.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-5 sm:p-6">
          {error && <p className="rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Почта</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-12 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-100"
              autoComplete="email"
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-12 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-100"
              autoComplete="current-password"
              required
            />
          </div>

          <div>
            <button
              type="submit"
              className="h-12 w-full rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={loading || !email.trim() || !password}
            >
              {loading ? "Входим..." : "Войти"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
