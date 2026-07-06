import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";

import { server } from "../mocks/server";

const memoryStorage = (() => {
  const storage = new Map<string, string>();
  return {
    getItem: (key: string) => (storage.has(key) ? storage.get(key)! : null),
    setItem: (key: string, value: string) => {
      storage.set(key, String(value));
    },
    removeItem: (key: string) => {
      storage.delete(key);
    },
    clear: () => {
      storage.clear();
    },
  };
})();

Object.defineProperty(globalThis, "localStorage", {
  value: memoryStorage,
  writable: true,
});

beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => {
  server.resetHandlers();
  cleanup();
  globalThis.localStorage.clear();
});
afterAll(() => server.close());
