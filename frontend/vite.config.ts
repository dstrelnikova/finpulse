import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup/setupTests.ts"],
    include: ["src/test/**/*.test.ts", "src/test/**/*.test.tsx"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      lines: 60,
      functions: 60,
      branches: 50,
      statements: 60,
    },
  },
});
