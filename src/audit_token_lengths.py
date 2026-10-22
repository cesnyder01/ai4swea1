"""Audit pilot lengths with a transparent provisional Java-like tokenizer.

This is a planning diagnostic only. It must be rerun with the trained project
tokenizer before claiming that the assignment's 10--512-token rule is met.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\r\n]*|/\*.*?\*/|'
    r'[A-Za-z_$][\w$]*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||\+\+|--|'
    r'>>>=|>>>|>>|<<|->|::|[^\s]',
    re.DOTALL,
)


def provisional_tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def document_text(record: dict[str, Any]) -> str:
    comments = "\n".join(comment.get("text", "") for comment in record.get("comments", []))
    return f"{comments}\n{record['code']}" if comments else record["code"]


def read_records(path: Path) -> list[dict[str, Any]]:
    records = []
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


def summary(lengths: list[int], minimum: int, maximum: int) -> dict[str, Any]:
    usable = [length for length in lengths if minimum <= length <= maximum]
    return {
        "records": len(lengths),
        "minimum_observed": min(lengths, default=0),
        "maximum_observed": max(lengths, default=0),
        "mean_observed": round(sum(lengths) / len(lengths), 2) if lengths else 0,
        "below_minimum": sum(length < minimum for length in lengths),
        "above_maximum": sum(length > maximum for length in lengths),
        "within_range": len(usable),
    }


def run(input_path: Path, output_path: Path, summary_path: Path,
        minimum: int = 10, maximum: int = 512) -> dict[str, Any]:
    records = read_records(input_path)
    code_lengths = [len(provisional_tokens(record["code"])) for record in records]
    document_lengths = [len(provisional_tokens(document_text(record))) for record in records]
    retained = [
        record for record, length in zip(records, document_lengths) if minimum <= length <= maximum
    ]
    result = {
        "tokenizer": "provisional-java-like-lexical-v1",
        "final_tokenizer": False,
        "minimum": minimum,
        "maximum": maximum,
        "input_records": len(records),
        "code_only_lengths": summary(code_lengths, minimum, maximum),
        "method_plus_comments_lengths": summary(document_lengths, minimum, maximum),
        "provisional_retained_records": len(retained),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in retained:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    arguments.add_argument("--minimum", type=int, default=10)
    arguments.add_argument("--maximum", type=int, default=512)
    args = arguments.parse_args()
    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}", file=sys.stderr)
        return 2
    try:
        result = run(args.input, args.output, args.summary, args.minimum, args.maximum)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
