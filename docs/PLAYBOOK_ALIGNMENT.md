# Antinode Norma Playbook Alignment

This document aligns Antinode Norma’s marketing and product roadmap with the structure, cadence, and operating model used in the `ai-development-playbook` repository.

## Purpose

- Make it easier for teams to see how Antinode Norma initiatives map to the AI playbook phases.
- Provide a clear connection between product marketing work and engineering cadence.
- Help stakeholders use the same language for adoption, quality, and delivery.

## Alignment Principles

1. **Signal over noise**
   - Prioritise clear initiatives with measurable outputs.
   - Avoid long speculative lists; focus on actionable quarterly goals.

2. **Open source first**
   - Emphasise transparency, self-hosted compatibility, and community adoption.
   - Treat open-source workflows as the product’s competitive advantage.

3. **Engineering and marketing together**
   - Map product features, content, and community activities to the same high-level phases.
   - Align release readiness with quality, documentation, and contributor enablement.

## Phase Mapping

| AI Playbook Phase | Antinode Norma Focus | Example Initiatives |
|---|---|---|
| Discovery & Feasibility | Market fit, target personas, buyer problems | `MARKETING_COMPETITIVE_AND_TRENDS_GUIDE.md`, buy-side messaging, competitor matrix |
| Requirements & Grooming | Product goals, feature scope, open-source packaging | Starter experience, OpenRouter compatibility, `README`, issue labels |
| Design & Architecture | Solution design, modular output, integration architecture | Page object generation design, connector/plugin architecture, CLI/open plugin workflows |
| Development | Implementation quality, open-source extensibility | Mapping diagnostics, prompt transparency, reusable step libraries, community asset library |
| Testing & QA | Validation, CI, prompt/test coverage, drift detection | Playwright validation workflow, `GitHub Actions` templates, generated test quality checks |
| Deployment & CI/CD | Release process, automation, dependency management | Release notes automation, GitHub Actions CI, dependency scanning |
| Operations | Monitoring adoption, community health, roadmap updates | Community contribution process, quarterly roadmap cadence, public release schedule |
| Governance & Compliance | Transparency, docs, maintainability | Open prompts, schema docs, contribution guidelines, license and governance statements |

## Quarterly Roadmap Alignment

### Q2 2026

- Publish an open-source starter bundle and quickstart experience.
- Add CI validation flows and GitHub Actions templates for generated Playwright tests.
- Document OpenRouter and self-hosted LLM support in a dedicated integration guide.
- Launch contribution primers, issue labels, and public roadmap visibility.
- Surface prompt transparency and mapping diagnostics in the main docs.

### Q3 2026

- Implement reusable selector registries and shared page object patterns.
- Add failure analysis reporting for generated automation and drift detection.
- Publish migration guides from Cucumber/Behave/recorders into Antinode Norma.
- Create a `docs/PLAYBOOK_ALIGNMENT.md` section linking Antinode Norma workflows with playbook phases.
- Automate release-related documentation and dependency hygiene.

### Long-Term Radar (H2 2026)

- Explore conversational workflows for issue tracking and test generation.
- Evaluate self-healing selector suggestions and failure-driven mapping updates.
- Build fleet health reporting for open-source users.
- Publish shared asset libraries and example integration projects.
- Formalise a quarterly release review process aligned with the AI playbook cadence.

## Cross-Reference Notes

- The AI playbook emphasises a living roadmap and weekly/monthly cadence. Antinode Norma should mirror that by updating the roadmap regularly and linking product progress to community milestones.
- Use GitHub Actions and CI badges as trust signals for open-source adoption, matching the playbook’s emphasis on automated quality.
- When publishing documentation, include both developer-facing guides and stakeholder-facing positioning notes.

## Recommended Next Steps

1. Add a `docs/PROFILE.md` or `docs/CONTRIBUTING.md` entry describing how contributors should reference the playbook when proposing roadmap changes.
2. Add a simple GitHub issue template for `roadmap initiative` requests.
3. Keep `docs/MARKETING_COMPETITIVE_AND_TRENDS_GUIDE.md` and `docs/PLAYBOOK_ALIGNMENT.md` in sync with quarterly roadmap updates.

---

This document should be reviewed each quarter alongside the Antinode Norma roadmap and the AI playbook roadmap to maintain consistency.
