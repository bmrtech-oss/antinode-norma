from pathlib import Path

from antinode_aegis.facts import FactCatalog, FactProvenance, KnowledgeFact


def test_fact_catalog_loads_curated_knowledge_graph_fixture():
    catalog = FactCatalog.from_yaml(Path("antinode_norma/knowledge_graph/facts.yml"))

    assert catalog.schema_version == 1
    assert len(catalog.facts) == 10
    assert catalog.facts[0].provenance.source == "curated-static"


def test_fact_schema_preserves_provenance_and_tags():
    fact = KnowledgeFact(
        id="fact-1201",
        subject="account",
        predicate="requires",
        object="mfa",
        contradiction_phrase="account does not require mfa",
        provenance=FactProvenance(
            source="policy://identity",
            source_version="2026.09",
            curator="security-team",
        ),
        tags=["identity", "security"],
    )

    assert fact.provenance.source_version == "2026.09"
    assert fact.tags == ["identity", "security"]