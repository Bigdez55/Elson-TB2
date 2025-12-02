import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    include: ['**/*.{test,spec}.{js,jsx,ts,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{js,jsx,ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/setupTests.ts',
        'src/mocks/**/*'
      ]
    },
    css: true
  }
});