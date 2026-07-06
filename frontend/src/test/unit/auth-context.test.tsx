import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../context/AuthContext";

const getMeMock = vi.fn();

vi.mock("../../api/me", () => ({
  getMe: () => getMeMock(),
}));

function Consumer() {
  const { auth } = useAuth();
  if (auth.status === "loading") return <div>loading</div>;
  if (auth.status === "anonymous") return <div>anonymous</div>;
  return <div>authenticated</div>;
}

describe("AuthProvider", () => {
  it("falls back to anonymous when /me fails", async () => {
    localStorage.setItem("accessToken", "bad-token");
    getMeMock.mockRejectedValueOnce(new Error("401"));

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("anonymous")).toBeInTheDocument();
    });
    expect(localStorage.getItem("accessToken")).toBeNull();
    expect(localStorage.getItem("refreshToken")).toBeNull();
  });

  it("becomes authenticated when /me succeeds", async () => {
    localStorage.setItem("accessToken", "ok-token");
    getMeMock.mockResolvedValueOnce({ id: 1, email: "u@x.com", roles: ["user"], permissions: ["chat:use"] });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("authenticated")).toBeInTheDocument();
    });
  });
});
