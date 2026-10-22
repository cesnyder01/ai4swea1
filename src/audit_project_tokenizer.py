"""Measure project-tokenizer lengths and create the approved mined subset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import sentencepiece as spm

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from load_example import PREFIX, task_file
from src.audit_token_lengths import document_text
from src.deduplicate_methods import read_records


def describe(lengths: list[int], minimum: int, maximum: int) -> dict[str, Any]:
    ordered = sorted(lengths)
    within = sum(minimum <= length <= maximum for length in lengths)
    return {
        "records": len(lengths),
        "minimum_observed": min(lengths, default=0),
        "maximum_observed": max(lengths, default=0),
        "mean_observed": round(sum(lengths) / len(lengths), 2) if lengths else 0,
        "p50": ordered[len(ordered) // 2] if ordered else 0,
        "p90": ordered[int(len(ordered) * 0.90)] if ordered else 0,
        "p95": ordered[int(len(ordered) * 0.95)] if ordered else 0,
        "below_minimum": sum(length < minimum for length in lengths),
        "above_maximum": sum(length > maximum for length in lengths),
        "longer_than_512_fraction": round(
            sum(length > maximum for length in lengths) / len(lengths), 6
        )
        if lengths
        else 0,
        "within_range": within,
    }


def token_length(processor: spm.SentencePieceProcessor, text: str) -> int:
    return len(processor.encode(text, out_type=int))


def read_task_lengths(
    processor: spm.SentencePieceProcessor,
    root: Path,
    task: str,
    split: str,
) -> dict[str, Any]:
    source_lengths: list[int] = []
    target_lengths: list[int] = []
    path = task_file(root, task, split)
    with path.open(encoding="utf-8", newline="") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                source_value, target_value = line.rstrip("\r\n").split("\t", 1)
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: expected source<TAB>target") from exc
            source_lengths.append(
                token_length(processor, PREFIX[task] + source_value)
            )
            target_lengths.append(token_length(processor, target_value))
    return {
        "path": str(path),
        "rows": len(source_lengths),
        "input_with_prefix": describe(source_lengths, 10, 512),
        "target": describe(target_lengths, 10, 512),
    }


def write_valid_records(
    processor: spm.SentencePieceProcessor,
    input_path: Path,
    output_path: Path,
    minimum: int,
    maximum: int,
) -> tuple[int, int]:
    records, malformed = read_records(input_path)
    if malformed:
        raise ValueError(f"{input_path} contains {malformed} malformed records")
    retained = [
        record
        for record in records
        if minimum
        <= token_length(processor, document_text(record))
        <= maximum
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in retained:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    return len(records), len(retained)


def run(
    corpus_path: Path,
    tokenizer_path: Path,
    task_root: Path,
    output_path: Path,
    summary_path: Path,
    minimum: int = 10,
    maximum: int = 512,
) -> dict[str, Any]:
    processor = spm.SentencePieceProcessor(model_file=str(tokenizer_path))
    records, malformed = read_records(corpus_path)
    if malformed:
        raise ValueError(f"{corpus_path} contains {malformed} malformed records")
    corpus_lengths = [
        token_length(processor, document_text(record)) for record in records
    ]
    source_lengths = [
        token_length(processor, record["code"]) for record in records
    ]
    valid_records = [
        record
        for record, length in zip(records, corpus_lengths)
        if minimum <= length <= maximum
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in valid_records:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")

    tasks = {
        task: {
            split: read_task_lengths(processor, task_root, task, split)
            for split in ("train", "val", "test")
        }
        for task in PREFIX
    }
    result: dict[str, Any] = {
        "tokenizer": str(tokenizer_path),
        "tokenizer_type": "SentencePiece Unigram",
        "vocab_size": processor.get_piece_size(),
        "minimum": minimum,
        "maximum": maximum,
        "corpus": {
            "input": str(corpus_path),
            "code_only": describe(source_lengths, minimum, maximum),
            "method_plus_comments": describe(corpus_lengths, minimum, maximum),
            "retained_records": len(valid_records),
            "removed_records": len(records) - len(valid_records),
        },
        "tasks": tasks,
        "output": str(output_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("corpus", type=Path)
    arguments.add_argument("--tokenizer", type=Path, required=True)
    arguments.add_argument("--task-root", type=Path, required=True)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    arguments.add_argument("--minimum", type=int, default=10)
    arguments.add_argument("--maximum", type=int, default=512)
    args = arguments.parse_args()
    try:
        result = run(
            args.corpus,
            args.tokenizer,
            args.task_root,
            args.output,
            args.summary,
            args.minimum,
            args.maximum,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
