import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import AdminUsers from "../../pages/AdminUsers";

const listUsersMock = vi.fn();
const setUserRolesMock = vi.fn();

vi.mock("../../api/adminUsers", () => ({
  listUsers: (params: unknown) => listUsersMock(params),
  setUserRoles: (userId: number, roles: string[]) => setUserRolesMock(userId, roles),
}));

describe("AdminUsers page", () => {
  it("renders rows and applies role change", async () => {
    listUsersMock.mockResolvedValue({
      items: [
        { id: 1, email: "u1@example.com", name: "U1", roles: ["user"], created_at: "2026-01-01T00:00:00Z" },
      ],
      total: 1,
      page: 1,
      page_size: 5,
    });
    setUserRolesMock.mockResolvedValue({ ok: true });

    render(
      <MemoryRouter
        initialEntries={["/admin/users?page=1&page_size=5"]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/admin/users" element={<AdminUsers />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText("u1@example.com")).toBeInTheDocument();

    const roleSelect = screen
      .getAllByRole("combobox")
      .find((element) => (element as HTMLSelectElement).value === "user");
    expect(roleSelect).toBeDefined();

    fireEvent.change(roleSelect as HTMLSelectElement, { target: { value: "pro" } });

    await waitFor(() => {
      expect(setUserRolesMock).toHaveBeenCalledWith(1, ["pro"]);
    });
  });

  it("shows error text when loading fails", async () => {
    listUsersMock.mockRejectedValueOnce({ response: { data: { detail: "Forbidden" } } });

    render(
      <MemoryRouter initialEntries={["/admin/users"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/admin/users" element={<AdminUsers />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText("Forbidden")).toBeInTheDocument();
  });
});
