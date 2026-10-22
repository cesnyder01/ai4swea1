"""Deduplicate extracted Java-method JSONL records using explicit comparison keys."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


WHITESPACE = re.compile(r"\s+")


def normalize_for_comparison(value: str) -> str:
    """Normalize whitespace without changing the original source value."""
    return WHITESPACE.sub(" ", value).strip()


def method_key(record: dict[str, Any]) -> str:
    return normalize_for_comparison(record["code"])


def instance_key(record: dict[str, Any]) -> str:
    comments = [
        {
            "kind": comment.get("kind", ""),
            "role": comment.get("role", ""),
            "text": normalize_for_comparison(comment.get("text", "")),
        }
        for comment in record.get("comments", [])
    ]
    payload = {"code": method_key(record), "comments": comments}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def record_sort_key(record: dict[str, Any]) -> tuple[str, str, int, int, str]:
    provenance = record["provenance"]
    return (
        str(provenance["repository"]),
        str(provenance["file"]),
        int(provenance["start_line"]),
        int(provenance["end_line"]),
        str(record["id"]),
    )


def read_records(path: Path) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    malformed = 0
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record is not a JSON object")
                for field in ("id", "code", "comments", "provenance"):
                    if field not in record:
                        raise ValueError(f"missing required field: {field}")
                records.append(record)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                malformed += 1
                print(f"{path}:{line_number}: {exc}", file=sys.stderr)
    return records, malformed


def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ordered = sorted(records, key=record_sort_key)
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in ordered:
        by_method[method_key(record)].append(record)
        by_instance[instance_key(record)].append(record)

    retained: list[dict[str, Any]] = []
    for group in by_instance.values():
        record = dict(group[0])
        record["comparison"] = {
            "method_sha256": hashlib.sha256(method_key(record).encode()).hexdigest(),
            "instance_sha256": hashlib.sha256(instance_key(record).encode()).hexdigest(),
        }
        retained.append(record)
    retained.sort(key=record_sort_key)
    summary = {
        "input_records": len(records),
        "unique_normalized_methods": len(by_method),
        "duplicate_method_records": len(records) - len(by_method),
        "unique_normalized_instances": len(by_instance),
        "duplicate_instance_records": len(records) - len(by_instance),
    }
    return retained, summary


def run(input_path: Path, output_path: Path, summary_path: Path) -> dict[str, int]:
    records, malformed = read_records(input_path)
    retained, summary = deduplicate(records)
    summary["malformed_records"] = malformed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in retained:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    args = arguments.parse_args()
    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}", file=sys.stderr)
        return 2
    summary = run(args.input, args.output, args.summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["malformed_records"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
