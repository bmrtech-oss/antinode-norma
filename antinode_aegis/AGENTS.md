# Aegis Package Guidance

- Keep shared contracts, evidence, and normalization responsibilities within this package; avoid duplicating Norma application workflows here.
- When changing evidence requirements or matrix behavior, update the related tests and `docs/adr/evidence-matrix.yml` together.
- Validate evidence-matrix changes with `python -m antinode_aegis.evidence docs/adr/evidence-matrix.yml`.
- Preserve compatibility at the shared IR and adapter boundaries used by Norma and other consumers.