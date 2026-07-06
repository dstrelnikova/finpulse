import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Login from "../../pages/Login";

const loginUserMock = vi.fn();
const loginContextMock = vi.fn();
const navigateMock = vi.fn();

vi.mock("../../api/auth", () => ({
  loginUser: (payload: unknown) => loginUserMock(payload),
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({
    login: (tokens: { accessToken: string; refreshToken: string }) => loginContextMock(tokens),
  }),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const mod = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...mod,
    useNavigate: () => navigateMock,
  };
});

describe("Login page", () => {
  it("submits form and navigates to profile on success", async () => {
    loginUserMock.mockResolvedValueOnce({ access_token: "a", refresh_token: "r" });

    render(<Login />);

    const emailInput = document.querySelector('input[autocomplete="email"]') as HTMLInputElement;
    const passwordInput = document.querySelector('input[autocomplete="current-password"]') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: "user@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Войти" }));

    await waitFor(() => {
      expect(loginUserMock).toHaveBeenCalled();
      expect(loginContextMock).toHaveBeenCalledWith({ accessToken: "a", refreshToken: "r" });
      expect(navigateMock).toHaveBeenCalledWith("/profile");
    });
  });

  it("shows backend error message on failed login", async () => {
    loginUserMock.mockRejectedValueOnce({
      response: { data: { detail: "Incorrect email or password" } },
    });

    render(<Login />);

    const emailInput = document.querySelector('input[autocomplete="email"]') as HTMLInputElement;
    const passwordInput = document.querySelector('input[autocomplete="current-password"]') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: "user@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Войти" }));

    expect(await screen.findByText("Incorrect email or password")).toBeInTheDocument();
  });
});
