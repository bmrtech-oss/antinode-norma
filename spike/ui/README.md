# Aegis UI Spike

This directory is a non-production proof of concept for the Aegis foundation
profile. Open `index.html` directly in a browser; it has no build-time or
runtime dependencies.

## Findings

- The existing React shell in `ui/src/components/AppShell.tsx` already provides
  navigation, responsive layout, theme support, and accessible status patterns.
- Existing primitives in `ui/src/components/ui/` are sufficient for a future
  evidence, escalation, feature-flag, and release-gate surface.
- Aegis APIs for those surfaces do not exist yet. The spike therefore uses
  static placeholders and explicitly does not add production routes or fetches.
- The layout uses cards and a status notice that can be composed from the
  existing `Card`, `Badge`, and `Alert` primitives when the P5-P8 contracts
  become available.

## Recommendation

**Go for incremental UI integration after the Aegis API contracts exist.**
Keep this spike outside the production bundle, and do not expose controls or
status claims until each surface has a versioned contract and evidence record.

The fallback is a CLI-only release if the responsive layout or accessibility
review fails.
