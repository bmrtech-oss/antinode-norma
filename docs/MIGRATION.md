# NORMA-BDD v4 -> v5 Data Migration Guide

**Document:** `docs/MIGRATION.md`
**Task:** H2-T01 (Phase H2 — Enterprise Completeness)
**Status:** Approved & Implemented
**Date:** 2026-09-21

---

## 1. Overview

This document describes the automated, idempotent data migration path from Antinode Norma v4 file-based artifacts (`features/`, `stories/`, and `norma.config.yml`) to the v5 database schema format.

Migration logic is implemented in `antinode_norma/core/migrate_v4.py`.

---

## 2. CLI Command Usage

### Dry-Run Validation (Recommended First Step)
To preview the migration and verify file counts without modifying state:

```bash
python -m antinode_norma.core.migrate_v4 --source . --dry-run
```

### Execution
To execute the migration against the target environment:

```bash
python -m antinode_norma.core.migrate_v4 --source .
```

---

## 3. Idempotency & Rollback Policy

1. **Idempotency:** Re-running the migration against an already migrated directory updates existing schema rows cleanly without duplicating feature or story entities.
2. **Rollback:** In destructive migration scenarios, a pre-migration database snapshot (`VACUUM INTO` for SQLite or `pg_dump` for Postgres) is created automatically. If errors occur during migration, run:

```bash
# SQLite Rollback
cp build/backup_pre_migration.db build/norma.db
```
