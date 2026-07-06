import { NavLink, NavLinkProps } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

type LinkProps = NavLinkProps & {
  children: React.ReactNode;
};

const Link = ({ to, children, ...props }: LinkProps) => (
  <NavLink
    to={to}
    {...props}
    className={({ isActive }) =>
      "rounded-md px-3 py-2 text-sm font-semibold transition " +
      (isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950")
    }
  >
    {children}
  </NavLink>
);

export default function Navbar() {
  const { auth, hasPermission, hasRole, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLogoutOpen, setIsLogoutOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const isLoading = auth.status === "loading";
  const isAuthed = auth.status === "authenticated";

  useEffect(() => {
    if (!isLogoutOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsLogoutOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isLogoutOpen]);

  useEffect(() => {
    if (!isMenuOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsMenuOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isMenuOpen]);

  async function confirmLogout() {
    setIsLoggingOut(true);
    try {
      await logout();
    } finally {
      setIsLoggingOut(false);
      setIsLogoutOpen(false);
    }
  }

  return (
    <>
      <nav className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <NavLink
            to="/"
            className="flex min-w-0 items-center gap-3"
            onClick={() => setIsMenuOpen(false)}
          >
            <img src="/icon.png" alt="" className="h-9 w-9 rounded-md" />
            <div className="min-w-0">
              <p className="truncate text-lg font-bold leading-tight text-slate-950">FinPulse</p>
              <p className="hidden text-xs font-medium text-slate-500 sm:block">рынок РФ без лишнего шума</p>
            </div>
          </NavLink>

          <button
            type="button"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-navigation"
            onClick={() => setIsMenuOpen((value) => !value)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700 transition hover:bg-slate-50 md:hidden"
          >
            <span className="sr-only">Открыть меню</span>
            <span className="text-xl leading-none">{isMenuOpen ? "×" : "≡"}</span>
          </button>

          <div className="hidden items-center gap-1 md:flex">
            <Link to="/news/public">Новости</Link>
            <Link to="/market/moex">MOEX</Link>

            {isLoading ? (
              <span className="px-3 py-2 text-sm text-slate-400">Проверка...</span>
            ) : isAuthed ? (
              <>
                {hasPermission("chat:use") && <Link to="/chat">Чат</Link>}
                {hasPermission("profile:read_own") && <Link to="/profile">Профиль</Link>}
                {hasRole("admin") && <Link to="/admin/users">Управление</Link>}
                <button
                  type="button"
                  onClick={() => setIsLogoutOpen(true)}
                  className="rounded-md px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
                >
                  Выйти
                </button>
              </>
            ) : (
              <>
                <Link to="/login">Войти</Link>
                <NavLink
                  to="/register"
                  className="ml-1 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  Регистрация
                </NavLink>
              </>
            )}
          </div>
        </div>

        {isMenuOpen && (
          <div id="mobile-navigation" className="border-t border-slate-200 bg-white px-4 py-3 shadow-sm md:hidden">
            <div className="grid gap-1">
              <Link to="/news/public" onClick={() => setIsMenuOpen(false)}>Новости</Link>
              <Link to="/market/moex" onClick={() => setIsMenuOpen(false)}>MOEX</Link>

              {isLoading ? (
                <span className="px-3 py-2 text-sm text-slate-400">Проверка сессии...</span>
              ) : isAuthed ? (
                <>
                  {hasPermission("chat:use") && <Link to="/chat" onClick={() => setIsMenuOpen(false)}>Чат</Link>}
                  {hasPermission("profile:read_own") && <Link to="/profile" onClick={() => setIsMenuOpen(false)}>Профиль</Link>}
                  {hasRole("admin") && <Link to="/admin/users" onClick={() => setIsMenuOpen(false)}>Управление</Link>}
                  <button
                    type="button"
                    onClick={() => {
                      setIsMenuOpen(false);
                      setIsLogoutOpen(true);
                    }}
                    className="rounded-md px-3 py-2 text-left text-sm font-semibold text-slate-600 transition hover:bg-slate-100"
                  >
                    Выйти
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setIsMenuOpen(false)}>Войти</Link>
                  <Link to="/register" onClick={() => setIsMenuOpen(false)}>Регистрация</Link>
                </>
              )}
            </div>
          </div>
        )}
      </nav>

      {isLogoutOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/40 px-4 py-6 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="logout-title"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setIsLogoutOpen(false);
          }}
        >
          <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white shadow-xl">
            <div className="border-b border-gray-100 px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                Завершение сессии
              </p>
              <h2 id="logout-title" className="mt-1 text-2xl font-semibold text-gray-950">
                Выйти из FinPulse?
              </h2>
            </div>

            <div className="px-5 py-5">
              <p className="text-sm leading-relaxed text-gray-600">
                Текущая сессия будет завершена. Чтобы вернуться в личный кабинет и чат,
                нужно будет снова войти в аккаунт.
              </p>
            </div>

            <div className="flex flex-col-reverse gap-2 border-t border-gray-100 px-5 py-4 sm:flex-row sm:justify-end">
              <button
                type="button"
                disabled={isLoggingOut}
                className="h-11 rounded-md border border-gray-200 px-4 text-sm font-semibold text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-300"
                onClick={() => setIsLogoutOpen(false)}
              >
                Остаться
              </button>
              <button
                type="button"
                disabled={isLoggingOut}
                className="h-11 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                onClick={() => void confirmLogout()}
              >
                {isLoggingOut ? "Выходим..." : "Выйти"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
