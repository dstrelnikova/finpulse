import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RequireAuth, RequirePermission } from "../../context/guards";

const useAuthMock = vi.fn();

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => useAuthMock(),
}));

describe("route guards", () => {
  it("redirects anonymous user to login", () => {
    useAuthMock.mockReturnValue({
      auth: { status: "anonymous" },
      hasPermission: () => false,
      hasRole: () => false,
    });

    render(
      <MemoryRouter initialEntries={["/private"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route
            path="/private"
            element={
              <RequireAuth>
                <div>Private</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects authenticated user without permission to 403", () => {
    useAuthMock.mockReturnValue({
      auth: { status: "authenticated", me: { id: 1, roles: ["user"], permissions: [] } },
      hasPermission: () => false,
      hasRole: () => false,
    });

    render(
      <MemoryRouter initialEntries={["/private"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route
            path="/private"
            element={
              <RequirePermission permission="admin_users:list">
                <div>Private</div>
              </RequirePermission>
            }
          />
          <Route path="/403" element={<div>Forbidden page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Forbidden page")).toBeInTheDocument();
  });

  it("renders children when permission is granted", () => {
    useAuthMock.mockReturnValue({
      auth: { status: "authenticated", me: { id: 1, roles: ["admin"], permissions: ["admin_users:list"] } },
      hasPermission: (p: string) => p === "admin_users:list",
      hasRole: () => true,
    });

    render(
      <MemoryRouter initialEntries={["/private"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route
            path="/private"
            element={
              <RequirePermission permission="admin_users:list">
                <div>Private</div>
              </RequirePermission>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Private")).toBeInTheDocument();
  });
});
