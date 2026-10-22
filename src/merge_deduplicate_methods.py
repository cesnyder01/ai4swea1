"""Merge decontaminated JSONL files and deduplicate them globally."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.deduplicate_methods import deduplicate, instance_key, read_records


def run(inputs: list[Path], output_path: Path, summary_path: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    input_counts: dict[str, int] = {}
    for input_path in inputs:
        if not input_path.is_file():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        source_records, malformed = read_records(input_path)
        if malformed:
            raise ValueError(f"{input_path} contains {malformed} malformed records")
        input_counts[str(input_path)] = len(source_records)
        records.extend(source_records)

    retained, dedup_summary = deduplicate(records)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[instance_key(record)].append(record)
    cross_repository_duplicates = sum(
        len(group) - 1
        for group in groups.values()
        if len({record.get("provenance", {}).get("repository") for record in group}) > 1
    )
    summary: dict[str, Any] = {
        "input_files": [str(path) for path in inputs],
        "input_counts": input_counts,
        **dedup_summary,
        "cross_repository_duplicate_records": cross_repository_duplicates,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in retained:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("inputs", type=Path, nargs="+")
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    args = arguments.parse_args()
    try:
        summary = run(args.inputs, args.output, args.summary)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
