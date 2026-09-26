from pathlib import Path

from antinode_norma.knowledge_graph.store import KnowledgeGraphStore


def test_kuzu_adapter_preserves_catalog_provenance_and_tags():
    store = KnowledgeGraphStore(Path("antinode_norma/knowledge_graph/facts.yml"))

    facts = store.facts()

    assert len(facts) == 10
    assert facts[0]["provenance"]["source"] == "curated-static"
    assert facts[0]["tags"] == []


def test_kuzu_adapter_queries_contradictions():
    store = KnowledgeGraphStore(Path("antinode_norma/knowledge_graph/facts.yml"))

    matches = store.find_contradictions("The reset link remains valid forever.")

    assert [fact["id"] for fact in matches] == ["reset-link-expiry"]