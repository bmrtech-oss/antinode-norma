"""Commercial Aegis audit-event schema and append-only ledger."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


GENESIS_HASH = "0" * 64


class AuditEvent(BaseModel):
    """Versioned governance event with tenant and actor context."""

    schema_version: int = 1
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tenant_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    result: str = "success"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    previous_hash: str = GENESIS_HASH
    content_hash: str = ""

    def content_for_hash(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"content_hash"})

    def calculate_hash(self) -> str:
        payload = json.dumps(self.content_for_hash(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditLedger:
    """Append-only JSONL ledger for Aegis governance events."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("build/aegis_audit.jsonl")
        self.events: List[AuditEvent] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        self.events = [
            AuditEvent.model_validate(json.loads(line))
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def append(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            metadata=metadata or {},
            previous_hash=self.events[-1].content_hash if self.events else GENESIS_HASH,
        )
        event.content_hash = event.calculate_hash()
        self.events.append(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(), sort_keys=True) + "\n")
        return event

    def verify_integrity(self) -> bool:
        previous = GENESIS_HASH
        for event in self.events:
            if event.previous_hash != previous or event.content_hash != event.calculate_hash():
                return False
            previous = event.content_hash
        return True
