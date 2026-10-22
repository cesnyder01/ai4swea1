# CSCI 680 Assignment 1 Project Setup

This repository contains the provided fine-tuning data package in
`code-and-comment-to-code/` and `code-to-comment/`. Stage 1 adds the
reproducible project scaffold, environment checks, and planning documents
needed before any mining or model training begins.

## What Stage 1 accomplishes

- Confirms the local machine setup and records the baseline environment.
- Creates the folder layout for corpus mining, tokenizer training, experiments, results, and docs.
- Adds a lightweight environment-check script that can run before machine-learning packages are installed.
- Sets up a project-local Python virtual environment for reproducible development.
- Documents the assignment requirements and the next steps in plain language.

## Current status

- Existing fine-tuning data package: present; its current second-task files are
  nested under `code-to-comment/code-to-comment/`, and the loader supports both
  that layout and the documented top-level layout.
- Part 1 pilot extractor: verified on one pinned MIT-licensed repository
  (`adobe/log-parser`): 44 Java files, 479 methods, 269 with comments, 210
  code-only, and 0 extraction failures. This is not the 300,000-instance target.
- Local Git repository: present.
- Python available: yes, Python 3.13.7.
- Git available: yes.
- NVIDIA GPU tooling: not detected locally.
- Full corpus mining, tokenizer training, pretraining, fine-tuning, and evaluation: not started.

## Recommended commands for Stage 1

From the project root in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\src\check_environment.py
pytest
```

If PowerShell blocks activation scripts, run this once for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

## Roadmap

1. Record candidate MIT-licensed Java repositories from GitHub Search.
2. Run a tiny, inspectable mining pilot on one repository.
3. Verify one Tree-sitter extraction pilot manually, then add filtering,
   deduplication, and decontamination scripts.
4. Train the assignment tokenizer on the mined corpus.
5. Run pretraining, fine-tuning, and evaluation only after the data pipeline is stable.

## Notes for this repository

- Use relative paths from the project root.
- Keep large datasets, checkpoints, and secrets out of Git.
- Record decisions in `docs/decisions_log.md` as the project evolves.
- Record data provenance in `docs/data_sources.md`.
- Record AI assistance, prompts, model information, and response summaries in
  `docs/ai_disclosure_log.md` for the assignment writeup.
- Complete `corpus/manifests/repository_selection.csv` from your own GHS
  searches before cloning or mining repositories.
- The pilot output is local and ignored by Git; inspect it manually before
  selecting additional repositories.

## Existing package documentation

The rest of this README documents the supplied fine-tuning data package and its provenance. That content is preserved below so the assignment data stays understandable and traceable.

# Code review automation — fine-tuning data for CSCI 680 (Fall 2026)

**Data card.** Built 2026-09-25 for the assignment *Does Pre-training Earn Its Keep?*
Every number below was computed by `build_package.py` from the files in this folder; `stats.json` has the full set, including what was repaired and what was dropped before sampling.

## Provenance and license

- Source: Tufano, Masiero, Mastropaolo, Pascarella, Poshyvanyk, Bavota. *Using Pre-Trained Models to Boost Code Review Automation.* ICSE 2022 (arXiv:2201.06850). Replication package: <https://github.com/RosaliaTufano/code_review_automation>.
- Derived from the `new_large` fine-tuning splits of Zenodo record [10.5281/zenodo.5387856](https://doi.org/10.5281/zenodo.5387856) (`dataset.zip`, published 2021-09-02, license **CC BY 4.0**). The Zenodo files have 134,239 / 16,780 / 16,780 rows per task; this package is a **repaired, filtered and seed-sampled subset** of them (see *How this package was derived*). `SHA256SUMS` covers the files here; `SHA256SUMS.zenodo-originals` the files they were derived from.
- Not included, on purpose: the record's `pre-training.tsv`, its SentencePiece tokenizer and every checkpoint. The assignment forbids them; you mine your own corpus and train your own tokenizer. The record's third task, `code-to-code`, is not part of the assignment and is not included either.
- Mined from Java projects on GitHub and Gerrit; the paper describes the mining and filtering. Reviewer comments are real, written by real people, sometimes blunt.

## Files

```
code-and-comment-to-code/{train,val,test}.tsv     50,000 / 5,000 / 5,000 rows
code-to-comment/{train,val,test}.tsv              50,000 / 5,000 / 5,000 rows
stats.json                    every statistic in this card, machine-readable
SHA256SUMS                    sha256sum -c SHA256SUMS   (the files in this folder)
SHA256SUMS.zenodo-originals   checksums of the Zenodo files these were derived from
load_example.py               a 20-line loader that adds the task prefixes
```

Format: one instance per line, `source<TAB>target`, no header, UTF-8, no quoting. Split on the **first** tab only (`line.split("\t", 1)`); do not use `csv.reader` with default quoting, the code contains quote characters. Whitespace inside methods is already normalized to single spaces.

## The two tasks

| Task | Source | Target |
|---|---|---|
| `code-and-comment-to-code` | `<code>` method with the reviewed span wrapped in `<START>` … `<END>` `</code><technical_language>` reviewer comment `</technical_language>` | the revised method, as the developer submitted it after the review |
| `code-to-comment` | the method submitted for review (no markers) | the reviewer's comment, verbatim |

Task prefixes for the assignment: `code&comment2code: ` and `code2comment: ` (see `load_example.py`).

**Row i is the same review instance in both tasks**, in every split: the `code-to-comment` method appears verbatim inside the `code-and-comment-to-code` source in every row (50,000 / 50,000 train, 5,000 / 5,000 test), and the comment inside `<technical_language>` is the `code-to-comment` target, verbatim, in every row (50,000 / 50,000 train). The multi-task mix is therefore straightforward, and **decontamination is done once, against the union of both tasks' validation and test sets**.

## How this package was derived

Everything below was done by `build_package.py`, deterministically (seed 680); nothing was hand-edited.

1. **Repairs to the `code&comment-to-code` input.** The Zenodo files carry two artefacts of the original preprocessing. (a) The reviewer comment inside `<technical_language>` had been passed through a stop-word filter (*"don't return NULL, throw …"* had become *"return NULL, throw …"*); it was replaced by the verbatim comment from row *i* of `code-to-comment` (125,463 / 15,663 / 15,638 rows of the original splits; the rest were already identical). (b) In some rows the closing marker appeared as a bare `END>` token; it was rewritten to `<END>` (1,599 / 200 / 192 rows). The pattern never occurs inside code or in a target, so the rewrite is unambiguous.
2. **Rows dropped** (train / val / test of the original splits): missing `<START>` or `<END>` marker, so the reviewed span is unknown: 35 / 7 / 5; a `<LINK_n>` placeholder in the comment, standing for a URL the original mining removed: 2,501 / 310 / 337; method not identical between the two tasks: 3 / 0 / 0. Eligible after dropping: 131,700 / 16,463 / 16,438.
3. **Sampling.** 50,000 / 5,000 / 5,000 rows drawn uniformly at random from the eligible rows of each original split (`random.Random(680).sample`), the same indices for both tasks, original order preserved. Validation and test rows come from the original validation and test splits only, so the paper's separation of projects between splits is inherited.

Consequence for comparisons with the paper: the paper's models saw 134,239 training pairs with stop-word-stripped comments and were tested on 16,780 rows; yours see 50,000 pairs with verbatim comments and are tested on 5,000. Its numbers are a reference point, not a target.

## Counts and lengths (whitespace-separated words; token counts depend on your tokenizer)

| Task | Split | Rows | Source words p50 / p90 / max | Target words p50 / p90 / max |
|---|---|---|---|---|
| code-and-comment-to-code | train | 50,000 | 65 / 140 / 422 | 44 / 114 / 333 |
| code-and-comment-to-code | val | 5,000 | 64 / 139 / 287 | 43 / 114 / 245 |
| code-and-comment-to-code | test | 5,000 | 66 / 140 / 329 | 45 / 114 / 257 |
| code-to-comment | train | 50,000 | 46 / 116 / 271 | 13 / 38 / 403 |
| code-to-comment | val | 5,000 | 46 / 115 / 246 | 13 / 38 / 277 |
| code-to-comment | test | 5,000 | 47 / 116 / 245 | 13 / 39 / 299 |

The longest sources are about 300 words; under a subword tokenizer a share of them will exceed 512 tokens. Measure that share under *your* tokenizer and say what you do with them (truncate, drop, or raise the limit; the same choice for every model).

## Integrity checks (all splits)

- Exact duplicate pairs within any split: **0**. Duplicate sources within any split: **0**. Source identical to target: **0**.
- Validation / test pairs that also appear in train: **0**. Validation / test *sources* that appear in train: **0**.
- Validation / test **targets** that also appear as a train target: `code-and-comment-to-code` 11 / 11; `code-to-comment` 241 / 238 (short, generic comments recur; the most frequent repeated validation targets are 'final', 'static import', 'why?', "Extract the building of the ResponseMessage to it's own variable (in eclipse, select the text, right-click > refactor > extract local variable / select code + shift+alt+L). This will make the code a bit more readable, especially when you'll be passing in other things besides the ResponseMessage."; that is the data, not leakage of an instance).
- Validation ∩ test pairs: **0** in both tasks.
- Every `code-and-comment-to-code` source carries both `<START>` and `<END>`: 50,000 / 5,000 / 5,000. Bare `END>` tokens: 0. `<LINK_n>` placeholders: 0. Targets never contain the markers.
- A few sources contain HTML or XML inside string literals (`<html>`, `<td>`, …). They are code, not markup; do not strip tags.

## Rules of use in this course

1. **Validation sets select checkpoints. Test sets are used once, by each final model.** Nothing else touches them.
2. **Decontaminate your pre-training corpus** against every validation and test *source method* and *target* of both tasks, after whitespace normalization, and report how many instances you removed.
3. Whatever normalization you apply before exact match (whitespace, and nothing that changes tokens), apply it identically to every model and state it once.
4. Redistribution follows CC BY 4.0: cite the ICSE 2022 paper and the Zenodo record.

## Example (test row 0, both tasks)

`code-to-comment` target: *Let's add a constant for "version 2"*

`code-and-comment-to-code` source (end of the string): `…True(pckIn.readString() == PacketLineIn.END); return recvStream; }</code><technical_language>Let's add a constant for "version 2"</technical_language>`
