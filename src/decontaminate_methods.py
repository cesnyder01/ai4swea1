"""Remove mined records overlapping held-out fine-tuning inputs or targets."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.deduplicate_methods import normalize_for_comparison
from load_example import task_file


HELD_OUT_SPLITS = ("val", "test")
TASKS = ("code-and-comment-to-code", "code-to-comment")


def load_held_out_values(root: Path) -> tuple[dict[str, set[str]], int]:
    values: dict[str, set[str]] = defaultdict(set)
    rows = 0
    for task in TASKS:
        for split in HELD_OUT_SPLITS:
            path = task_file(root, task, split)
            with path.open(encoding="utf-8", newline="") as source:
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    try:
                        source_value, target_value = line.rstrip("\r\n").split("\t", 1)
                    except ValueError as exc:
                        raise ValueError(f"{path}:{line_number}: expected source<TAB>target") from exc
                    values[normalize_for_comparison(source_value)].add(f"{task}/{split}:source")
                    values[normalize_for_comparison(target_value)].add(f"{task}/{split}:target")
                    rows += 1
    return dict(values), rows


def record_values(record: dict[str, Any]) -> set[str]:
    values = {normalize_for_comparison(record["code"])}
    values.update(
        normalize_for_comparison(comment["text"])
        for comment in record.get("comments", [])
        if comment.get("text")
    )
    return values


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record is not a JSON object")
                records.append(record)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON record: {exc}") from exc
    return records


def run(input_path: Path, task_root: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    records = read_records(input_path)
    held_out_values, held_out_rows = load_held_out_values(task_root)
    retained: list[dict[str, Any]] = []
    removals: list[dict[str, Any]] = []
    reason_counts: dict[str, int] = defaultdict(int)
    for record in records:
        matches = sorted(
            source
            for value in record_values(record)
            for source in held_out_values.get(value, set())
        )
        if matches:
            removals.append({"id": record["id"], "matches": matches})
            for match in matches:
                reason_counts[match] += 1
        else:
            retained.append(record)

    summary = {
        "input_records": len(records),
        "held_out_rows": held_out_rows,
        "held_out_comparison_values": len(held_out_values),
        "removed_records": len(removals),
        "retained_records": len(retained),
        "removal_reason_counts": dict(sorted(reason_counts.items())),
        "removed_record_ids": removals,
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
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--task-root", type=Path, required=True)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    args = arguments.parse_args()
    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}", file=sys.stderr)
        return 2
    try:
        summary = run(args.input, args.task_root, args.output, args.summary)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({key: value for key, value in summary.items() if key != "removed_record_ids"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
