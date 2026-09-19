from antinode_norma.governance.audit import AuditLog


def test_audit_log_record_and_hash_chain(tmp_path):
    log_file = tmp_path / "test_audit.jsonl"
    audit = AuditLog(log_path=log_file)

    e1 = audit.record_event(action="generate_feature", resource="account_transfers.feature", actor="alice")
    e2 = audit.record_event(action="run_gates", resource="account_transfers.feature", actor="bob")

    assert e1.previous_hash == "0" * 64
    assert e2.previous_hash == e1.content_hash
    assert len(audit.records) == 2
    assert audit.verify_integrity() is True


def test_audit_log_persistence_and_reload(tmp_path):
    log_file = tmp_path / "test_audit.jsonl"
    audit1 = AuditLog(log_path=log_file)
    audit1.record_event(action="approve_feature", resource="account_transfers.feature", actor="reviewer1")

    audit2 = AuditLog(log_path=log_file)
    assert len(audit2.records) == 1
    assert audit2.records[0].action == "approve_feature"
    assert audit2.verify_integrity() is True


def test_audit_log_tamper_detection(tmp_path):
    log_file = tmp_path / "test_audit.jsonl"
    audit = AuditLog(log_path=log_file)
    audit.record_event(action="create", resource="res1")
    audit.record_event(action="update", resource="res1")

    # Simulate log tampering
    audit.records[0].action = "tampered_action"
    assert audit.verify_integrity() is False
