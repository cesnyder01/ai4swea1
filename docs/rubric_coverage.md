# Assignment Rubric Coverage

This checklist maps the official assignment PDF and the additional rubric
requirements supplied in chat to the artifact that will provide evidence. The
PDF is `C:\Users\corae\Downloads\T5-code-review-wm (1).pdf` (six pages,
released 2026-09-28). It is not copied into the repository. It is intentionally
conservative: `complete` means
the requirement has been implemented and verified, `incomplete` means work
remains, and `blocked` means the authoritative assignment PDF or another
required input is unavailable.

## Authority and evidence

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Treat the assignment PDF as authoritative | complete | Local PDF path above; this checklist | The PDF was provided and read. The checklist must be updated if the PDF changes. |
| Maintain a requirement-to-artifact checklist | incomplete | This file | The checklist exists and is reconciled to the supplied PDF, but final evidence does not yet exist. |
| Explain decisions, avoid invented results, and maintain AI disclosure | incomplete | [ai_disclosure_log.md](ai_disclosure_log.md), [decisions_log.md](decisions_log.md) | Disclosure logging is active. Final decisions and results do not yet exist. |

## Corpus construction

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Select MIT-licensed Java repositories using documented GHS evidence | incomplete | [repository_selection.csv](../corpus/manifests/repository_selection.csv), [data_sources.md](data_sources.md) | The GHS site, snapshot date, result count, unrestricted stars/commits/size/activity fields, selection criteria, repositories, licenses, and SHAs are now recorded. The 300,000 usable-instance target has not been reached. |
| Remove exact and near duplicates before other filters | incomplete | [deduplicate_methods.py](../src/deduplicate_methods.py), [near_deduplicate_methods.py](../src/near_deduplicate_methods.py), `results/metrics/global.near-deduplication.json` | Policy implemented at 0.90 ordered-token similarity with a 10-token minimum; diagnostic removed 51,416 records after exact deduplication. Final ordering from mined records, representative review, and the reconciled all-stage count table are still required. |
| Record removals by every corpus-processing step and reconcile counts | incomplete | `results/metrics/`, [data_sources.md](data_sources.md) | Current extraction, local deduplication, decontamination, parse filtering, global deduplication, and provisional length reports exist. A final reconciled count table is still required. |
| Decontaminate against the union of both tasks' validation/test sources and targets | complete | [decontaminate_methods.py](../src/decontaminate_methods.py), `results/metrics/*decontamination.json` | The current pipeline compares both source and target values from both validation and test splits. Final-corpus rerun remains required. |
| Reach at least 300,000 usable instances | incomplete | `results/metrics/global.*` | Current global count is 64,975 before final tokenizer filtering; 61,439 are only provisionally length-valid. |

## Tokenizer

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Train a fresh tokenizer only on the mined corpus | incomplete | `tokenizer/` (planned), `src/` (training script planned) | No project tokenizer has been trained. The PDF permits a new SentencePiece Unigram/BPE or Hugging Face tokenizer; pretrained tokenizers are prohibited. |
| Report and justify tokenizer type and vocabulary size | incomplete | `docs/tokenizer.md` (planned), tokenizer config (planned) | Architecture and vocabulary size require a documented decision. |
| Add T5 sentinel tokens and `<START>`/`<END>` | incomplete | tokenizer configuration and test report (planned) | Not implemented. |
| Report corpus and task input/output token-length distributions | incomplete | `results/metrics/token_lengths.json` (planned) | Current length results use a provisional lexer only. |
| Report and document task examples longer than 512 tokens | incomplete | tokenizer length report (planned) | No actual-tokenizer task audit exists. The provided task data must not be rewritten. |

## Pretraining

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Initialize T5 weights from scratch | incomplete | pretraining config, model code, run log (planned) | The PDF specifies T5-small by default, constructed from `T5Config` and `T5ForConditionalGeneration(config)`, never `from_pretrained`. |
| Use span corruption with 15% masking | incomplete | corruption implementation, config, examples (planned) | The configuration records `0.15`; implementation and verification are absent. |
| Report mean span length | incomplete | pretraining config/report (planned) | The example config records 3; the actual sampled distribution must be measured. |
| Show two real corruption input/target pairs | incomplete | `results/pretraining/corruption_examples.json` (planned) | Not generated. |
| Reserve 1% of the corpus for pretraining evaluation | incomplete | split manifest and config (planned) | The configuration records `0.01`; the split and seed evidence are absent. |
| Record training/held-out loss and masked-token accuracy | incomplete | training logs, curves, metrics table (planned) | No pretraining run exists. |
| Use bf16 or fp32 | incomplete | training configuration and hardware log (planned) | Precision choice is not yet implemented or recorded. |

## Fine-tuning

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Do not filter, clean, or rewrite supplied fine-tuning data | incomplete | checksums, data audit report (planned) | The files are present and loader support exists; final checksum verification and immutable-input audit must be recorded. |
| Verify the supplied ZIP using its instructions | incomplete | ZIP verification report (planned) | The confirmed ZIP/checksum artifacts need a reproducible verification record. |
| Never use test data for training or checkpoint selection | incomplete | split manifest, training logs, configuration (planned) | No training run exists to verify. |
| Run random initialization condition A before pretrained condition B | incomplete | experiment manifest and timestamps (planned) | No fine-tuning runs exist. |
| Use exact prefixes `code&comment2code:` and `code2comment:` | incomplete | [config.example.yaml](../configs/config.example.yaml), loader tests, run config | Prefixes are configured, but end-to-end training use is not verified. |
| Use a balanced 50/50 task mix | incomplete | training manifest and batch statistics (planned) | No multitask loader exists. |
| Keep all other experimental factors fixed | incomplete | paired experiment manifest (planned) | No paired experiments exist. |

## Evaluation

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Use greedy decoding | incomplete | evaluation config and prediction manifest (planned) | The PDF specifies greedy decoding with beam width 1. No evaluator exists. |
| Report exact-match counts and percentages overall and per confidence bucket | incomplete | evaluation report and prediction CSVs (planned) | No predictions exist. |
| Choose and report a confidence threshold and coverage | incomplete | evaluation report (planned) | No confidence scores exist. |
| Report CodeBLEU for code-to-code and BLEU-4 for code-to-comment with named settings | incomplete | metrics configuration/report (planned) | Metric implementation and settings are absent. |
| Manually label 25 incorrect predictions per task | incomplete | annotation CSV/report (planned) | No predictions exist. |
| Record sequence probability on a 0–100 scale for every test prediction | incomplete | prediction CSV schema and validation (planned) | No evaluator or prediction CSV exists. |

## Reproducibility and completion

| Requirement | Status | Evidence artifact(s) | Notes |
|---|---|---|---|
| Preserve exact commands, seeds, pinned requirements, curves, data card, predictions, and links | incomplete | `README.md`, `docs/`, `results/`, `requirements*.txt`, manifests (planned) | The PDF requires exact commands from mining through evaluation, seeds, pinned requirements, a corpus data card, prediction CSVs, and links to checkpoints/corpus. Existing setup and corpus logs are partial; experiment artifacts do not exist. Large checkpoints must remain outside Git. |
| Produce required prediction CSV columns | incomplete | `results/<task>-<condition>.csv` (planned) | Each row must include `task`, `condition`, `input`, `expected`, `predicted`, `correct`, and `score`, with quoted CSV fields. |
| Submit the three-page LaTeX write-up with disclosure block | incomplete | Blackboard PDF (not repository artifact) | The PDF requires a three-page write-up covering Parts 1–4 and a disclosure block. |
| Do not implement the bonus before required work is sound | complete | This checklist, [assignment_requirements.md](assignment_requirements.md) | No bonus implementation has been started. |
| If implementing the bonus, match the specified budget/schedule and task exposure | blocked | Bonus experiment manifest (planned) | Do not begin until the required experiments are complete and the PDF is available. |
| Generate a final rubric coverage report before declaring completion | incomplete | This file | This is an initial coverage report and must be updated after every major stage and finalized at project completion. |

## Current blockers and decisions needed

1. Provide the official assignment PDF, or place it in the repository so this
   checklist can be reconciled against the authoritative wording.
2. Decide the tokenizer type and vocabulary size after reviewing the PDF's
   precise constraints, if it specifies any.
3. Define the near-duplicate method and similarity threshold before final
   corpus filtering; do not silently treat whitespace normalization as
   near-duplicate detection.
4. Confirm the permitted compute budget before selecting a T5 model size and
   training schedule.
