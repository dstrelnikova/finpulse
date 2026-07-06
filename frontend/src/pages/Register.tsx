import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth";
import SeoHead from "../components/SeoHead";
import { getApiErrorMessage } from "../api/errors";

const Register: React.FC = () => {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setErrorMsg("Введите имя");
      return;
    }
    if (password !== confirm) {
      setErrorMsg("Пароли не совпадают");
      return;
    }

    setErrorMsg(null);
    setSubmitting(true);

    try {
      await registerUser({ name, email, password });

      // MVP: после регистрации отправляем на логин
      // (можно заменить на onboarding/profile позже)
      navigate("/login");
    } catch (err: unknown) {
      console.error("Ошибка регистрации", err);
      setErrorMsg(getApiErrorMessage(err, "Не удалось зарегистрироваться. Попробуйте ещё раз."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <SeoHead
        title="Регистрация | FinPulse"
        description="Создайте аккаунт FinPulse для персональной ленты и AI-помощника."
        canonicalPath="/register"
      />
      <div className="mx-auto max-w-xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-950 px-5 py-5 text-white sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">Аккаунт</p>
          <h1 className="mt-1 text-2xl font-semibold">Регистрация</h1>
          <p className="mt-2 text-sm text-slate-300">Создайте профиль для персональной ленты и AI-чата.</p>
        </div>

      {errorMsg && (
        <div className="mx-5 mt-5 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 sm:mx-6">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 px-5 py-5 sm:px-6">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Имя</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="h-12 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-100"
            autoComplete="name"
            required
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Почта</label>
          <input
            type="email"
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
            autoComplete="new-password"
            required
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Подтвердите пароль</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="h-12 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-100"
            autoComplete="new-password"
            required
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={submitting || !name.trim() || !email.trim() || !password || !confirm}
            className="h-12 w-full rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitting ? "Регистрирую…" : "Зарегистрироваться"}
          </button>
        </div>
      </form>

        <div className="border-t border-slate-100 px-5 py-4 text-sm leading-relaxed text-slate-500 sm:px-6">
          Настройки ленты сохраняются по умолчанию: Россия и MOEX. После регистрации их можно изменить в профиле кнопкой «Сохранить изменения».
        </div>
      </div>
    </>
  );
};

export default Register;
