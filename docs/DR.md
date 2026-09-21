# NORMA-BDD Disaster Recovery (DR) & Backup Policy

**Document:** `docs/DR.md`
**Task:** H2-T02 (Phase H2 — Enterprise Completeness)
**Status:** Approved & Implemented
**Date:** 2026-09-21

---

## 1. Executive Summary

This document defines the Disaster Recovery (DR), database snapshot backup, retention, and restore drill policies for the Antinode Norma platform.

- **Recovery Time Objective (RTO):** ≤ 1 hour
- **Recovery Point Objective (RPO):** ≤ 15 minutes

---

## 2. Backup & Restore Architecture

The backup mechanism is implemented in `antinode_norma/core/backup.py`.

- **Online Database Snapshots:** Uses SQLite `VACUUM INTO` for lock-free online snapshot creation.
- **Postgres Archiving:** Uses `pg_dump --format=custom` plus WAL archiving for multi-node deployments.
- **Integrity Check:** Pre- and post-restore integrity checks are executed using `PRAGMA quick_check`.

---

## 3. Retention & Backup Schedule

| Backup Type | Frequency | Retention Window | Storage Location |
|---|---|---|---|
| **Hot Snapshots** | Every 15 minutes | 24 hours | Local Volume (`build/backups/`) |
| **Daily Snapshots** | Daily at 02:00 UTC | 7 days | Secondary Cloud Storage / Offsite |
| **Quarterly Drill** | Quarterly | Archive | Offline DR Vault |

---

## 4. Restore Drill Procedure

To execute a restore drill or emergency restore:

1. **Verify Backup File Integrity:**
   ```bash
   sqlite3 build/backups/norma_backup.db "PRAGMA quick_check;"
   ```

2. **Execute Automated Restore API / Function:**
   ```python
   from pathlib import Path
   from antinode_norma.core.backup import restore_backup

   result = restore_backup(
       backup_path=Path("build/backups/norma_backup.db"),
       db_path=Path("build/norma.db"),
   )
   assert result["status"] == "success"
   ```

3. **Validate Row Counts:**
   Confirm row counts and table structure match expected pre-disaster metrics.
