"""Remove conservative near-duplicate method instances with token-set Jaccard."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit_token_lengths import provisional_tokens
from src.deduplicate_methods import instance_key, read_records, record_sort_key


HASH_COUNT = 64
BANDS = 8
ROWS_PER_BAND = HASH_COUNT // BANDS


def token_sequence(record: dict[str, Any]) -> tuple[str, ...]:
    comments = " ".join(comment.get("text", "") for comment in record.get("comments", []))
    return tuple(provisional_tokens(f"{comments}\n{record['code']}"))


def token_set(record: dict[str, Any]) -> frozenset[str]:
    return frozenset(token_sequence(record))


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def sequence_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    return SequenceMatcher(a=left, b=right, autojunk=False).ratio()


def hash_value(token: str, seed: int) -> int:
    digest = hashlib.blake2b(
        f"{seed}:{token}".encode("utf-8"), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big")


def signature(tokens: frozenset[str]) -> tuple[int, ...]:
    if not tokens:
        return (0,) * HASH_COUNT
    return tuple(min(hash_value(token, seed) for token in tokens) for seed in range(HASH_COUNT))


def candidate_pairs(
    signatures: list[tuple[int, ...]],
) -> set[tuple[int, int]]:
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = defaultdict(list)
    for index, values in enumerate(signatures):
        for band in range(BANDS):
            start = band * ROWS_PER_BAND
            buckets[(band, values[start : start + ROWS_PER_BAND])].append(index)
    pairs: set[tuple[int, int]] = set()
    for members in buckets.values():
        for offset, left in enumerate(members):
            for right in members[offset + 1 :]:
                pairs.add((left, right))
    return pairs


def near_deduplicate(
    records: list[dict[str, Any]], threshold: float = 0.90, minimum_tokens: int = 10
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    ordered = sorted(records, key=record_sort_key)
    token_sequences = [token_sequence(record) for record in ordered]
    token_sets = [frozenset(tokens) for tokens in token_sequences]
    signatures = [signature(tokens) for tokens in token_sets]
    pairs = candidate_pairs(signatures)
    instance_keys = {instance_key(record) for record in ordered}
    exact_duplicate_records = len(ordered) - len(instance_keys)
    duplicate_of: dict[int, int] = {}
    duplicate_pairs: list[dict[str, Any]] = []
    short_records_skipped = sum(len(tokens) < minimum_tokens for tokens in token_sequences)
    for left, right in sorted(pairs):
        if right in duplicate_of:
            continue
        if (
            len(token_sequences[left]) < minimum_tokens
            or len(token_sequences[right]) < minimum_tokens
        ):
            continue
        similarity = sequence_similarity(token_sequences[left], token_sequences[right])
        if similarity >= threshold:
            duplicate_of[right] = left
            duplicate_pairs.append(
                {
                    "representative_id": ordered[left]["id"],
                    "removed_id": ordered[right]["id"],
                    "similarity": round(similarity, 6),
                    "representative_provenance": ordered[left]["provenance"],
                    "removed_provenance": ordered[right]["provenance"],
                }
            )
    retained = [
        record for index, record in enumerate(ordered) if index not in duplicate_of
    ]
    summary = {
        "input_records": len(records),
        "threshold": threshold,
        "minimum_tokens": minimum_tokens,
        "similarity": "SequenceMatcher ratio over ordered tokens(method plus comments)",
        "candidate_pairs": len(pairs),
        "candidate_pairs_checked": len(pairs),
        "exact_duplicate_records_in_input": exact_duplicate_records,
        "short_records_skipped": short_records_skipped,
        "near_duplicate_records_removed": len(duplicate_of),
        "retained_records": len(retained),
        "near_duplicate_groups": len(set(duplicate_of.values())),
    }
    return retained, summary, duplicate_pairs


def run(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    pairs_path: Path,
    threshold: float = 0.90,
    minimum_tokens: int = 10,
) -> dict[str, Any]:
    records, malformed = read_records(input_path)
    if malformed:
        raise ValueError(f"{input_path} contains {malformed} malformed records")
    retained, summary, duplicate_pairs = near_deduplicate(
        records, threshold, minimum_tokens
    )
    summary["malformed_records"] = malformed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pairs_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in retained:
            destination.write(json.dumps(record, ensure_ascii=True) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pairs_path.open("w", encoding="utf-8", newline="\n") as destination:
        for pair in duplicate_pairs:
            destination.write(json.dumps(pair, ensure_ascii=True) + "\n")
    return summary


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--summary", type=Path, required=True)
    arguments.add_argument("--pairs", type=Path, required=True)
    arguments.add_argument("--threshold", type=float, default=0.90)
    arguments.add_argument("--minimum-tokens", type=int, default=10)
    args = arguments.parse_args()
    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}", file=sys.stderr)
        return 2
    try:
        result = run(
            args.input,
            args.output,
            args.summary,
            args.pairs,
            args.threshold,
            args.minimum_tokens,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
