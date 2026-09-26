from antinode_aegis.audit import AuditLedger, GENESIS_HASH


def test_aegis_audit_schema_and_chain(tmp_path):
    ledger_path = tmp_path / "aegis-audit.jsonl"
    ledger = AuditLedger(path=ledger_path)

    first = ledger.append(
        tenant_id="tenant-1",
        actor_id="reviewer-1",
        action="feature.approved",
        resource_type="feature",
        resource_id="FEAT-801",
        metadata={"profile": "aegis-foundation"},
    )
    second = ledger.append(
        tenant_id="tenant-1",
        actor_id="reviewer-1",
        action="feature.released",
        resource_type="feature",
        resource_id="FEAT-801",
    )

    assert first.schema_version == 1
    assert first.previous_hash == GENESIS_HASH
    assert second.previous_hash == first.content_hash
    assert ledger.verify_integrity() is True


def test_aegis_audit_reload_and_tamper_detection(tmp_path):
    ledger_path = tmp_path / "aegis-audit.jsonl"
    ledger = AuditLedger(path=ledger_path)
    ledger.append(
        tenant_id="tenant-2",
        actor_id="system",
        action="generation.completed",
        resource_type="job",
        resource_id="JOB-802",
        result="success",
    )

    reloaded = AuditLedger(path=ledger_path)
    assert reloaded.verify_integrity() is True

    event = reloaded.events[0]
    event.result = "tampered"
    assert reloaded.verify_integrity() is False
