import csv
from pathlib import Path
from typing import List, Union, Dict, Any
from antinode_norma.core.types import TestCase
from antinode_norma.core.normalize import normalize_header, split_multi


class CSVIngester:
    """Ingests CSV test case rows into standardized TestCase instances."""

    def ingest(self, path: Union[str, Path]) -> List[TestCase]:
        csv_path = Path(path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        test_cases: List[TestCase] = []

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []

            # Map raw fieldnames to canonical names
            header_map: Dict[str, str] = {
                raw: normalize_header(raw) for raw in reader.fieldnames if raw
            }

            for idx, row in enumerate(reader, 1):
                mapped_row: Dict[str, Any] = {}
                metadata: Dict[str, Any] = {}

                for raw_header, val in row.items():
                    if not raw_header or val is None:
                        continue
                    norm_key = header_map.get(raw_header, normalize_header(raw_header))
                    if norm_key in {
                        "id",
                        "title",
                        "role",
                        "action",
                        "benefit",
                        "acceptance_criteria",
                        "tags",
                    }:
                        mapped_row[norm_key] = val
                    else:
                        metadata[norm_key] = val

                case_id = str(mapped_row.get("id") or f"TC-{idx:03d}").strip()
                title = str(mapped_row.get("title") or f"Test Case {idx}").strip()
                role = str(mapped_row.get("role") or "user").strip()
                action = str(mapped_row.get("action") or "").strip()
                benefit = str(mapped_row.get("benefit") or "").strip()

                raw_criteria = mapped_row.get("acceptance_criteria")
                acceptance_criteria = split_multi(raw_criteria)

                raw_tags = mapped_row.get("tags")
                tags = split_multi(raw_tags)

                test_cases.append(
                    TestCase(
                        id=case_id,
                        title=title,
                        role=role,
                        action=action,
                        benefit=benefit,
                        acceptance_criteria=acceptance_criteria,
                        tags=tags,
                        metadata=metadata,
                    )
                )

        return test_cases
