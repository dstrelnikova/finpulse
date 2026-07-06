import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type Props = {
  children: React.ReactNode;
};

export default function ProtectedRoute({ children }: Props) {
  const { auth } = useAuth();

  if (auth.status === "loading") {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 text-sm">
        Загрузка...
      </div>
    );
  }

  if (auth.status === "anonymous") {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}