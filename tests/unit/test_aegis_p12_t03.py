import pytest

from antinode_aegis.curation import FactCurationService
from antinode_aegis.facts import FactProvenance, KnowledgeFact


def fact(fact_id: str = "fact-1301", curator: str | None = "reviewer") -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        subject="account",
        predicate="requires",
        object="mfa",
        contradiction_phrase="account does not require mfa",
        provenance=FactProvenance(source="policy://identity", curator=curator),
    )


def test_curation_add_update_and_list():
    service = FactCurationService()
    service.add(fact())
    updated = service.update(fact(curator="security-team"))

    assert service.get("fact-1301") == updated
    assert service.list() == [updated]


def test_curation_rejects_duplicate_and_missing_curator():
    service = FactCurationService([fact()])

    with pytest.raises(ValueError, match="already exists"):
        service.add(fact())
    with pytest.raises(ValueError, match="curator is required"):
        service.add(fact("fact-1302", curator=None))
