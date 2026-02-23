// Created: 2026-01-14
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: false,
    environment: 'node',
    include: ['src/__tests__/sdk.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.test.ts', 'src/__mocks__/**', 'src/abis/**'],
    },
    testTimeout: 10000,
  },
});
