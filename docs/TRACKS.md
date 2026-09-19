# Track Coordination & Ownership — Antinode Norma

This document outlines the parallel track delivery model, file ownership, module freeze milestones, and convergence points.

---

## 1. Parallel Track Ownership

| Track | Domain & Focus | Lead Role | Owned Subsystems & Paths |
|---|---|---|---|
| **Track A** | Quality & Core Pipeline | QA Architect | `gates/`, `evaluate/`, `cache/`, `governance/`, `delivery/`, `server/mcp_server.py` |
| **Track B** | Execution Maturity | Engineering Lead | `execution/`, `codegen/`, `core/runner.py` |
| **Track C** | User-Facing & Platform | UX Lead | `ui/`, `server/api.py`, `server/routes/`, `server/auth/`, `collaboration/`, `analytics/` |

---

## 2. Code Freeze Milestones

To prevent merge conflicts across parallel tracks, shared core files are frozen after specific phase exits:

| File / Path | Frozen After Phase | Primary Owner |
|---|---|---|
| `core/agent.py` | Phase 4 (Walking Skeleton) | Track A |
| `core/types.py` | Phase 3b (Soft Gates) | Track A |
| `cli.py` | Phase 6 (MCP Tools) | Cross-Track |
| `server/api.py` | Phase 9-T02 (UI API Foundation) | Track C |

---

## 3. Convergence Milestones

- **P4 Convergence**: Walking skeleton completed; tracks fork into parallel execution (A, B, C).
- **P7 Convergence**: Governance and delivery wrap core agent outputs.
- **P11 Convergence**: Ecosystem plugin layer integrates with Track A quality gates, Track B execution runners, and Track C UI.
- **P12 Release Convergence**: Platform cross-track regression and final release packaging (v2.0.0).
