# UI Contrast and Status Audit — UI-2-T05

**ADR:** [ADR-009](adr/ADR-009-frontend-quality-and-theming.md)
**Scope:** `ui/` semantic tokens, status components, and primary views
**Standard:** WCAG 2.1 AA target

## Token review

The token pairs below are the required semantic combinations for content and controls. They must be checked in both `.light` and dark root states using an automated contrast tool when accessibility tooling is added.

| Token pair | Usage | Required check |
|---|---|---|
| `background` / `foreground` | Page text and background | Normal text AA |
| `card` / `card-foreground` | Cards, headers, shell | Normal text AA |
| `primary` / `primary-foreground` | Primary buttons and active navigation | Normal and large text AA |
| `secondary` / `secondary-foreground` | Secondary actions | Normal text AA |
| `muted` / `muted-foreground` | Supporting text and loading states | Normal text AA |
| `destructive` / `destructive-foreground` | Errors and destructive actions | Normal and large text AA |
| `success` / `success-foreground` | Successful state surfaces | Normal and large text AA |
| `warning` / `warning-foreground` | Warning state surfaces | Normal and large text AA |
| `border` / `background` | Structural boundaries | Non-text contrast where applicable |
| `ring` / adjacent background | Keyboard focus indicator | Focus appearance |

## Status communication rule

Status must never be communicated through color alone. Each status must include at least one additional channel:

- **Approved / verified:** explicit text plus check/shield icon.
- **Rejected / tampered:** explicit text plus X/alert/shield-alert icon.
- **Pending:** explicit text plus alert/pending icon.
- **Loading:** explicit text plus animated loader and `role="status"`.
- **Error:** explanatory text plus alert icon and an available retry action.

The approval, traceability, audit, loading, and error states now follow this rule. Icons that are decorative are marked `aria-hidden`; visible status words remain in the accessibility tree.

## Required validation

Before UI-2-T05 is considered fully evidenced:

1. Run an automated axe/contrast scan against every primary view in light and dark modes.
2. Verify normal text, large text, borders, controls, and focus indicators.
3. Complete a grayscale review to ensure status distinctions remain understandable without hue.
4. Complete keyboard review for focus visibility and status announcements.
5. Record tool versions, browser versions, and any exceptions in this document.

The repository currently has no browser accessibility runner configured. The semantic token audit and status-code review are committed now; automated scan evidence is a UI-4 task dependency.
