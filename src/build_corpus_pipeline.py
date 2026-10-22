"""Build the ordered, pre-tokenizer mined-corpus pipeline.

The assignment requires exact and near duplicates to be removed before later
quality filters and decontamination. Tokenizer-based length filtering is
intentionally not performed here because the project tokenizer does not exist
until this pipeline has been approved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.decontaminate_methods import run as decontaminate
from src.deduplicate_methods import deduplicate, read_records
from src.filter_parse_error_methods import affected_ranges
from src.near_deduplicate_methods import near_deduplicate


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in records:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")


def read_input_records(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Input file does not exist: {path}")
        source_records, malformed = read_records(path)
        if malformed:
            raise ValueError(f"{path} contains {malformed} malformed records")
        counts[str(path)] = len(source_records)
        records.extend(source_records)
    return records, counts


def filter_parse_errors(
    records: list[dict[str, Any]], report_path: Path
) -> tuple[list[dict[str, Any]], int]:
    ranges = affected_ranges(json.loads(report_path.read_text(encoding="utf-8")))
    retained: list[dict[str, Any]] = []
    removed = 0
    for record in records:
        provenance = record["provenance"]
        file_ranges = ranges.get(str(provenance["file"]).replace("\\", "/"), set())
        method_range = (int(provenance["start_line"]), int(provenance["end_line"]))
        if method_range in file_ranges:
            removed += 1
        else:
            retained.append(record)
    return retained, removed


def run(
    mined_dir: Path,
    task_root: Path,
    output_dir: Path,
    metrics_path: Path,
    parse_reports: list[Path] | None = None,
    threshold: float = 0.90,
    minimum_tokens: int = 10,
) -> dict[str, Any]:
    inputs = sorted(mined_dir.glob("*.methods.jsonl"))
    if not inputs:
        raise FileNotFoundError(f"No mined JSONL files found in {mined_dir}")
    parse_reports = parse_reports or []
    for report in parse_reports:
        if not report.is_file():
            raise FileNotFoundError(f"Parse-error report does not exist: {report}")

    records, input_counts = read_input_records(inputs)
    exact_records, exact_summary = deduplicate(records)
    near_records, near_summary, duplicate_pairs = near_deduplicate(
        exact_records, threshold, minimum_tokens
    )

    parse_filtered_records = near_records
    parse_removed = 0
    parse_report_summaries: list[dict[str, Any]] = []
    for report_path in parse_reports:
        parse_filtered_records, removed = filter_parse_errors(
            parse_filtered_records, report_path
        )
        parse_removed += removed
        parse_report_summaries.append(
            {"report": str(report_path), "removed_records": removed}
        )

    near_path = output_dir / "final.near-deduplicated.jsonl"
    parse_path = output_dir / "final.parse-filtered.jsonl"
    decontaminated_path = output_dir / "final.decontaminated.jsonl"
    exact_path = output_dir / "final.exact-deduplicated.jsonl"
    pairs_path = output_dir / "final.near-deduplication-pairs.jsonl"
    write_records(exact_path, exact_records)
    write_records(near_path, near_records)
    write_records(parse_path, parse_filtered_records)
    with pairs_path.open("w", encoding="utf-8", newline="\n") as destination:
        for pair in duplicate_pairs:
            destination.write(json.dumps(pair, ensure_ascii=True) + "\n")

    decontamination_summary_path = metrics_path.parent / "final.decontamination.json"
    decontamination_summary = decontaminate(
        parse_path, task_root, decontaminated_path, decontamination_summary_path
    )
    stages = [
        {
            "name": "extracted",
            "records_before": 0,
            "removed_records": 0,
            "records_after": len(records),
            "status": "complete",
        },
        {
            "name": "exact_deduplication",
            "records_before": len(records),
            "removed_records": len(records) - len(exact_records),
            "records_after": len(exact_records),
            "status": "complete",
        },
        {
            "name": "near_deduplication",
            "records_before": len(exact_records),
            "removed_records": len(exact_records) - len(near_records),
            "records_after": len(near_records),
            "status": "complete",
        },
        {
            "name": "approved_parse_error_filter",
            "records_before": len(near_records),
            "removed_records": parse_removed,
            "records_after": len(parse_filtered_records),
            "status": "complete",
        },
        {
            "name": "held_out_decontamination",
            "records_before": len(parse_filtered_records),
            "removed_records": decontamination_summary["removed_records"],
            "records_after": decontamination_summary["retained_records"],
            "status": "complete",
        },
        {
            "name": "project_tokenizer_length_filter",
            "records_before": decontamination_summary["retained_records"],
            "removed_records": None,
            "records_after": None,
            "status": "pending_tokenizer_training",
        },
    ]
    summary: dict[str, Any] = {
        "input_directory": str(mined_dir),
        "input_files": [str(path) for path in inputs],
        "input_counts": input_counts,
        "parse_error_reports": parse_report_summaries,
        "exact_deduplication": exact_summary,
        "near_deduplication": near_summary,
        "decontamination": decontamination_summary,
        "stages": stages,
        "outputs": {
            "exact_deduplicated": str(exact_path),
            "near_deduplicated": str(near_path),
            "parse_filtered": str(parse_path),
            "decontaminated": str(decontaminated_path),
            "near_duplicate_pairs": str(pairs_path),
        },
        "tokenizer_length_filter": {
            "status": "pending",
            "reason": "A fresh project tokenizer must be trained before measuring 10-512-token eligibility.",
        },
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--mined-dir", type=Path, required=True)
    arguments.add_argument("--task-root", type=Path, required=True)
    arguments.add_argument("--output-dir", type=Path, required=True)
    arguments.add_argument("--metrics", type=Path, required=True)
    arguments.add_argument("--parse-report", type=Path, action="append", default=[])
    arguments.add_argument("--threshold", type=float, default=0.90)
    arguments.add_argument("--minimum-tokens", type=int, default=10)
    args = arguments.parse_args()
    try:
        summary = run(
            args.mined_dir,
            args.task_root,
            args.output_dir,
            args.metrics,
            args.parse_report,
            args.threshold,
            args.minimum_tokens,
        )
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
