from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional

import kuzu
import yaml


class KnowledgeGraphStore:
    """Small Kuzu-backed fact store for the P4-T07 validation spike."""

    def __init__(self, facts_path: Optional[Path] = None):
        self.facts_path = facts_path or Path(__file__).with_name("facts.yml")
        self._workspace = Path(tempfile.mkdtemp(prefix="anorm-kg-"))
        self.connection = kuzu.Connection(kuzu.Database(str(self._workspace / "db")))
        self.connection.execute(
            "CREATE NODE TABLE Fact(id STRING PRIMARY KEY, subject STRING, "
            "predicate STRING, object STRING, contradiction_phrase STRING)"
        )
        self._load_facts()

    def _load_facts(self) -> None:
        data = yaml.safe_load(self.facts_path.read_text(encoding="utf-8")) or {}
        for fact in data.get("facts", []):
            self.connection.execute(
                "CREATE (f:Fact {id: $id, subject: $subject, predicate: $predicate, "
                "object: $object, contradiction_phrase: $contradiction_phrase})",
                {
                    "id": fact["id"],
                    "subject": fact["subject"],
                    "predicate": fact["predicate"],
                    "object": fact["object"],
                    "contradiction_phrase": fact["contradiction_phrase"],
                },
            )

    def facts(self) -> List[Dict[str, Any]]:
        result = self.connection.execute(
            "MATCH (f:Fact) RETURN f.id, f.subject, f.predicate, f.object, "
            "f.contradiction_phrase"
        )
        return [
            {
                "id": row[0],
                "subject": row[1],
                "predicate": row[2],
                "object": row[3],
                "contradiction_phrase": row[4],
            }
            for row in result.get_all()
        ]

    def find_contradictions(self, text: str) -> List[Dict[str, Any]]:
        normalized_text = " ".join(text.lower().split())
        return [
            fact
            for fact in self.facts()
            if fact["contradiction_phrase"].lower() in normalized_text
        ]
