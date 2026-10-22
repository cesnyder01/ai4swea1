"""Filter method records whose source ranges overlap reviewed parse errors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def affected_ranges(report: dict[str, Any]) -> dict[str, set[tuple[int, int]]]:
    return {
        file["file"].replace("\\", "/"): {
            (item["start_line"], item["end_line"])
            for item in file["methods_containing_error"]
        }
        for file in report["files"]
    }


def run(input_path: Path, report_path: Path, output_path: Path, summary_path: Path) -> dict[str, int]:
    ranges = affected_ranges(read_json(report_path))
    input_records = 0
    removed_records = 0
    retained_records = 0
    with input_path.open(encoding="utf-8") as source:
        records = []
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                provenance = record["provenance"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"{input_path}:{line_number}: invalid record: {exc}") from exc
            input_records += 1
            file_ranges = ranges.get(str(provenance["file"]).replace("\\", "/"), [])
            method_range = (int(provenance["start_line"]), int(provenance["end_line"]))
            if method_range in file_ranges:
                removed_records += 1
            else:
                records.append(record)
                retained_records += 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in records:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    summary = {
        "input_records": input_records,
        "removed_records": removed_records,
        "retained_records": retained_records,
        "reviewed_affected_methods": sum(len(values) for values in ranges.values()),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--report", type=Path, required=True)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    args = arguments.parse_args()
    try:
        summary = run(args.input, args.report, args.output, args.summary)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
