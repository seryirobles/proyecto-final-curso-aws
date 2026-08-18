import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import prettierConfig from 'eslint-config-prettier';

// Flat config, scoped to this toolchain root only. ESLint is invoked with
// cwd `frontend/`, so it cannot walk outward and reach `backend/` or
// `prototypes/` (docs/architecture.md section 3) — that isolation comes from
// how it is run, not from the ignores list below.
export default [
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}', 'tests/**/*.{js,jsx}'],
    ...react.configs.flat.recommended,
    languageOptions: {
      ...react.configs.flat.recommended.languageOptions,
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        globalThis: 'readonly',
      },
    },
    settings: {
      react: { version: 'detect' },
    },
  },
  {
    files: ['src/**/*.{js,jsx}', 'tests/**/*.{js,jsx}'],
    ...react.configs.flat['jsx-runtime'],
  },
  {
    files: ['src/**/*.{js,jsx}', 'tests/**/*.{js,jsx}'],
    ...reactHooks.configs.flat.recommended,
  },
  {
    files: ['*.config.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { process: 'readonly' },
    },
  },
  // Applied last so Prettier owns formatting and never fights ESLint over it.
  prettierConfig,
];
