# UI Guidance

- Follow the existing React, TypeScript, Vite, and Tailwind patterns in `src/`.
- Keep UI behavior covered by nearby Vitest tests; add Playwright coverage when a change affects a user workflow or accessibility.
- Use the package scripts for validation: `npm --prefix ui run lint`, `typecheck`, `test`, and `build` (or `npm --prefix ui run ci:ui`).
- Keep API assumptions aligned with the Python server schemas and routes.