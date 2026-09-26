import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str
    resource: str
    actor: str = "system"
    payload: Dict[str, Any] = Field(default_factory=dict)
    previous_hash: str = "0" * 64
    content_hash: str = ""

    def calculate_hash(self) -> str:
        data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "action": self.action,
            "resource": self.resource,
            "actor": self.actor,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
        }
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, log_path: Optional[Path] = None, database_url: Optional[str] = None):
        self.log_path = log_path or Path("build/audit_log.jsonl")
        self.database_url = database_url
        self.records: List[AuditRecord] = []
        if self.database_url:
            from antinode_norma.database import load_audit_events

            self.records = [AuditRecord(**item) for item in load_audit_events(self.database_url)]
        elif self.log_path.exists():
            self._load_from_file()

    def _load_from_file(self) -> None:
        self.records = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    record = AuditRecord(**data)
                    self.records.append(record)

    def record_event(
        self, action: str, resource: str, actor: str = "system", payload: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        prev_hash = self.records[-1].content_hash if self.records else "0" * 64
        record = AuditRecord(
            action=action,
            resource=resource,
            actor=actor,
            payload=payload or {},
            previous_hash=prev_hash,
        )
        record.content_hash = record.calculate_hash()
        self.records.append(record)
        if self.database_url:
            from antinode_norma.database import save_audit_event

            save_audit_event(self.database_url, record.model_dump())
        else:
            self._persist_record(record)
        return record

    def record_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success",
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        full_payload = dict(payload) if payload else {}
        full_payload.update(
            {
                "user_id": user_id,
                "result": result,
                "ip": ip or "127.0.0.1",
                "user_agent": user_agent or "unknown",
            }
        )
        return self.record_event(
            action=action,
            resource=resource,
            actor=user_id,
            payload=full_payload,
        )

    def _persist_record(self, record: AuditRecord) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.model_dump()) + "\n")

    def verify_integrity(self) -> bool:
        prev_hash = "0" * 64
        for record in self.records:
            if record.previous_hash != prev_hash:
                return False
            if record.content_hash != record.calculate_hash():
                return False
            prev_hash = record.content_hash
        return True
