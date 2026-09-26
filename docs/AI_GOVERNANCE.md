# AI Governance Register

**Status:** Foundation documentation; not a certification or conformity
assessment
**Release profile:** `aegis-foundation`
**Owner:** Platform Governance
**Last reviewed:** 2026-09-25

## Current implementation status

ADR-003 phases P4 through P13 have completed their recorded checkpoints for
the `aegis-foundation` workstream. The current next task is P14-T03 analytics
polish. The full Aegis release profiles remain not release-approved until the
profile-specific evidence, security review, and release-manager sign-off are
complete.

| Evidence surface | Current verification |
|---|---|
| Python regression | `python -m pytest -q` with external-provider tests requiring valid credentials or explicit skip handling |
| Cross-track regression | `tests/integration/test_cross_track_regression_p12_t01.py` |
| Frontend quality | `cd ui && npm run ci:ui` |
| Evidence matrix | `python -m antinode_aegis.evidence docs/adr/evidence-matrix.yml` |

This register defines the governance boundary for Aegis and distinguishes
controls that are evidenced in the current Norma workflow from target controls
that require later implementation. Customer-specific legal classification,
including EU AI Act Annex III applicability, must be confirmed during
onboarding with qualified legal and compliance reviewers.

## 1. Scope and accountability

Aegis is an evidence and governance layer for AI-assisted software and AI
systems. It does not replace customer risk management, legal review, security
incident response, or human release accountability.

| Role | Responsibility |
|---|---|
| Product Owner | Accepts release profile and residual product risk |
| Engineering Lead | Ensures implementation, rollback, and operational evidence |
| QA Architect | Owns quality-gate evidence and independent verification |
| Security Lead | Owns secrets, security findings, access control, and incident escalation |
| SME / designated reviewer | Resolves low-confidence or domain-sensitive decisions |
| Release Manager | Confirms profile-specific gates and records release sign-off |

## 2. Control register

| Governance theme | Current evidence | Target control / exit evidence |
|---|---|---|
| Risk management | ADR-003 risk register and escalation policy | Versioned risk assessment, owners, treatment decisions, and review dates |
| Data governance | Import provenance, ownership, retention, and secret-handling policies | Dataset register, minimization review, lineage, quality checks, and approved PII redaction |
| Technical documentation | ADR-003, evidence matrix, phase artifacts | Versioned system card, model/provider inventory, limitations, and change history |
| Record-keeping | Audit and evidence documentation in the Norma workflow | Immutable Aegis decision ledger with retention and export verification |
| Transparency | Release profile and current-versus-target boundaries are documented | User-facing notices for generated content, confidence, limitations, and human decisions |
| Human oversight | Approval workflow, escalation policy, and SME routing requirements | Enforced review queue, reviewer identity, decision reason, and override audit trail |
| Accuracy and robustness | Existing deterministic validation, focused tests, and cost gates | Calibrated evaluation, drift monitoring, adversarial tests, and release thresholds |
| Cybersecurity | Gitleaks, fail-fast secrets handling, rollback, and security escalation | Completed dependency/PII scans, threat model, incident drills, and reviewed findings |
| Post-market monitoring | Not implemented in the foundation profile | Incident, feedback, drift, and corrective-action process with scheduled review |

## 3. Framework mapping

### ISO/IEC 42001

The register supports an AI management-system workstream through documented
roles, risk ownership, evidence retention, incident escalation, and continual
improvement. It is not evidence of ISO/IEC 42001 certification. Certification
or an audit opinion requires an approved management system, an independent
assessment, and organization-specific evidence.

### EU AI Act

Potential Annex III applicability is customer-dependent. Before a customer
release, the customer and qualified reviewers must document:

1. Whether the system is in scope and which category applies.
2. The risk-management and data-governance obligations that apply.
3. Technical documentation, logging, human-oversight, accuracy, robustness,
   cybersecurity, and post-market monitoring evidence.
4. The responsible deployer/provider roles and escalation contacts.

The staged dates described in ADR-003 are planning context, not a legal
determination. Prohibited-practice, general-purpose, and high-risk obligations
must be checked against the applicable law and current guidance at release
time.

## 4. Operating rules

- A missing control is recorded as `planned`, `partial`, or `blocked`; it is
  never represented as passed because a document exists.
- Generated content and evaluation results require human accountability for
  release decisions.
- Secrets, raw PII, prompts, and generated content must not be placed in
  telemetry by default.
- Security findings and required-secret failures halt the relevant release
  path and follow [ESCALATION.md](ESCALATION.md).
- Every production-facing control must gain code, focused tests, and an
  evidence artifact before it is marked implemented in the evidence matrix.

## 5. Related controls

- [ADR-003-AEGIS.md](adr/ADR-003-AEGIS.md)
- [ESCALATION.md](ESCALATION.md)
- [SECRETS.md](SECRETS.md)
- [ROLLBACK.md](ROLLBACK.md)
- [COMPONENT_SOURCING.md](COMPONENT_SOURCING.md)
