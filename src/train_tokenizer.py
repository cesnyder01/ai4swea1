"""Train the project's fresh SentencePiece Unigram tokenizer."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import sentencepiece as spm

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit_token_lengths import document_text
from src.deduplicate_methods import read_records


SENTINEL_TOKENS = tuple(f"<extra_id_{index}>" for index in range(100))
USER_DEFINED_SYMBOLS = ("<START>", "<END>", *SENTINEL_TOKENS)


def write_training_text(input_path: Path, text_path: Path) -> int:
    records, malformed = read_records(input_path)
    if malformed:
        raise ValueError(f"{input_path} contains {malformed} malformed records")
    with text_path.open("w", encoding="utf-8", newline="\n") as destination:
        for record in records:
            destination.write(document_text(record).replace("\r", " ").replace("\n", " "))
            destination.write("\n")
    return len(records)


def train(
    input_path: Path,
    output_dir: Path,
    vocab_size: int = 32_128,
    seed: int = 680,
    model_type: str = "unigram",
) -> dict[str, Any]:
    if model_type != "unigram":
        raise ValueError("Only the assignment's selected Unigram tokenizer is supported")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tokenizer-", dir=output_dir) as temporary:
        text_path = Path(temporary) / "training.txt"
        records = write_training_text(input_path, text_path)
        prefix = output_dir / "java_review_unigram"
        spm.SentencePieceTrainer.train(
            input=str(text_path),
            model_prefix=str(prefix),
            vocab_size=vocab_size,
            model_type=model_type,
            character_coverage=1.0,
            input_sentence_size=0,
            shuffle_input_sentence=False,
            seed_sentencepiece_size=1_000_000,
            num_threads=1,
            normalization_rule_name="identity",
            unk_id=2,
            bos_id=-1,
            eos_id=1,
            pad_id=0,
            user_defined_symbols=list(USER_DEFINED_SYMBOLS),
        )
    processor = spm.SentencePieceProcessor(model_file=str(prefix) + ".model")
    metadata = {
        "tokenizer_type": "SentencePiece Unigram",
        "vocab_size": processor.get_piece_size(),
        "requested_vocab_size": vocab_size,
        "training_records": records,
        "training_input": str(input_path),
        "seed": seed,
        "normalization": "identity",
        "special_tokens": {
            "pad": processor.id_to_piece(0),
            "eos": processor.id_to_piece(1),
            "unk": processor.id_to_piece(2),
            "user_defined": list(USER_DEFINED_SYMBOLS),
        },
    }
    metadata_path = output_dir / "tokenizer_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("input", type=Path)
    arguments.add_argument("--output-dir", type=Path, required=True)
    arguments.add_argument("--vocab-size", type=int, default=32_128)
    arguments.add_argument("--seed", type=int, default=680)
    args = arguments.parse_args()
    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}", file=sys.stderr)
        return 2
    try:
        result = train(args.input, args.output_dir, args.vocab_size, args.seed)
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
