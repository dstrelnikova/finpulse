import { Routes, Route, Navigate } from "react-router-dom";

import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import PublicNews from "./pages/PublicNews";
import PublicNewsItem from "./pages/PublicNewsItem";
import MoexMarket from "./pages/MoexMarket";
import Profile from "./pages/Profile";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminUsers from "./pages/AdminUsers";
import NotFound from "./pages/NotFound";

import Navbar from "./components/Navbar";
import { RequirePermission } from "./context/guards";

function Forbidden() {
  return (
    <div className="mx-auto max-w-xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="bg-slate-950 px-6 py-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">Доступ</p>
        <h1 className="mt-1 text-2xl font-semibold">403 Forbidden</h1>
      </div>
      <p className="p-6 text-sm text-slate-600">У текущего аккаунта нет доступа к этому разделу.</p>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 lg:px-8">
        <Routes>
          {/* public */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/403" element={<Forbidden />} />
          <Route path="/news/public" element={<PublicNews />} />
          <Route path="/news/public/:slug" element={<PublicNewsItem />} />
          <Route path="/market/moex" element={<MoexMarket />} />

          <Route
            path="/chat"
            element={
              <RequirePermission permission="chat:use">
                <Chat />
              </RequirePermission>
            }
          />

          <Route path="/news" element={<Navigate to="/news/public" replace />} />

          <Route
            path="/profile"
            element={
              <RequirePermission permission="profile:read_own">
                <Profile />
              </RequirePermission>
            }
          />

          {/* admin */}
          <Route 
            path="/admin" 
            element={<Navigate to="/admin/users" replace />
            } 
          />

          <Route
            path="/admin/users"
            element={
              <RequirePermission permission="admin_users:assign_role">
                <AdminUsers />
              </RequirePermission>
            }
          />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}
