// Created: 2026-01-31
import {defineConfig} from 'vite';
import revideo from '@revideo/vite-plugin';

export default defineConfig({
  plugins: [
    revideo(),
  ],
});