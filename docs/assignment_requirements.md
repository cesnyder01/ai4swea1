# Assignment Requirements Summary

This file tracks the requirements we are implementing for CSCI 680 Assignment 1.

## Completed setup and pilot

- Inspect the existing workspace and environment.
- Create a reproducible project structure without deleting existing work.
- Set up a local Python virtual environment.
- Install only lightweight setup dependencies.
- Add an environment-check script and run it.
- Write setup instructions and a roadmap in the README.
- Run one bounded Tree-sitter extraction pilot with provenance and comment metadata.

## Current status

- Thirty-four repositories have been processed, audited, extracted,
  deduplicated, and decontaminated through the ordered pipeline. One additional
  candidate is pending a commit SHA.
- The current ordered pipeline contains 208,970 records within 10--512 tokens
  under the fresh 32,128-piece SentencePiece Unigram tokenizer.
- The repository target of at least 300,000 usable instances has not been met;
  91,030 additional usable records are still needed if the target is retained.
- The authoritative assignment PDF is not currently present in the workspace.
  Until it is provided, the supplied rubric requirements are tracked in
  [rubric_coverage.md](rubric_coverage.md).

## Later stages, not started yet

- Continue mining until the final tokenizer-measured corpus target is met.
- Train a tokenizer only from the approved mined corpus and report its
  vocabulary, sentinel tokens, and length distributions. This is complete for
  the current corpus; further repository selection may require retraining it.
- Pretrain T5 from scratch with the required span-corruption procedure.
- Fine-tune condition A before condition B on both assignment tasks.
- Evaluate with the required decoding, confidence, exact-match, CodeBLEU,
  BLEU-4, and manual-error-labeling artifacts.
- Produce and finalize the rubric coverage report.

## Important constraints

- Do not fabricate data, metrics, or repository metadata.
- Do not train on validation or test examples.
- Keep the mined corpus separate from the provided fine-tuning data.
- Decontamination against the union of both tasks' validation and test inputs and
  targets has been implemented and run for the current mined batch; it must be
  rerun after final corpus construction.
- Prefer reproducible scripts, relative paths, and logged configuration.
