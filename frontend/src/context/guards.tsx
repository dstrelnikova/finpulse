import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { auth } = useAuth();

  if (auth.status === "loading") return null;
  if (auth.status === "anonymous") return <Navigate to="/login" replace />;

  return <>{children}</>;
}

export function RequirePermission({
  permission,
  children,
}: {
  permission: string;
  children: React.ReactNode;
}) {
  const { auth, hasPermission } = useAuth();

  if (auth.status === "loading") return null;
  if (auth.status === "anonymous") return <Navigate to="/login" replace />;
  if (!hasPermission(permission)) return <Navigate to="/403" replace />;

  return <>{children}</>;
}

export function RequireRole({
  role,
  children,
}: {
  role: string;
  children: React.ReactNode;
}) {
  const { auth, hasRole } = useAuth();

  if (auth.status === "loading") return null;
  if (auth.status === "anonymous") return <Navigate to="/login" replace />;
  if (!hasRole(role)) return <Navigate to="/403" replace />;

  return <>{children}</>;
}