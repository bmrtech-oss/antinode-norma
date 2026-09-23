# AEGIS-P0 Escalation Policy Evidence

- **Requirement:** `AEGIS-P0-ESCALATION`
- **Release profile:** `aegis-foundation`
- **Phase:** P0
- **Task:** `P0-T05`
- **Verified:** 2026-09-23
- **Implementation:** `docs/ESCALATION.md`,
  `.github/ISSUE_TEMPLATE/blocked_task.md`

## Commands

```text
python -m pytest tests/unit/test_aegis_p0_escalation.py --no-cov -q
```

## Result

- ADR-003 escalation triggers and actions are present in the foundation policy.
- The policy defines two-attempt stop rules and human decision requirements.
- Escalation artifacts include a JSON summary and a blocked-task GitHub issue.
- The issue template captures task identity, trigger, evidence, remediation,
  required decision, and exit condition.
