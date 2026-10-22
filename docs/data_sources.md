# Data Sources

Use this document to record what data enters the project and how it was obtained.

## Repository selection log

The CSV at `corpus/manifests/repository_selection.csv` records the first selected
repository. One row must be completed for every candidate, including exclusions.
The search date is recorded as 2026-10-16 and the reported result count is
1,426. The current log records the GHS site `https://seart-ghs.si.usi.ch/` with no
keyword terms, MIT license, Java, creation dates 2020-01-01 through
2022-12-31, 3--15 contributors, and at least 30 comment lines for the
original batch. The new batch uses at least 1,000 comment lines and at least
50,000 nonblank, non-comment Java source lines. Stars,
commits, repository size, and activity were explicitly unrestricted. The
search result count was 1,426 on 2026-10-16. These values are recorded in the
manifest without inventing a more specific URL-encoded query.

- GitHub search query used for candidate repositories.
- Search date and selection criteria.
- Repository URLs and commit SHAs.
- License checks confirming MIT-only repositories.
- Any excluded repositories, with brief reasons.

For each candidate, use GitHub Search (GHS) and record the exact query and date.
Then verify that the repository's root license is MIT (not merely that it has a
MIT-licensed dependency), record the selected commit SHA, and retain the
repository URL. A pilot may use one selected repository; large-scale mining
must wait until the candidate list is confirmed.

## Pilot extraction

`src/extract_java_methods.py` recursively finds `.java` files, skips common
build/generated/vendor directories, parses Java with Tree-sitter, and writes
one JSON object per method to JSONL. Each record preserves the exact method
source and records repository, URL, commit, file, and line provenance. Adjacent
Javadoc/line/block comments and comments inside the method are recorded
separately, so code-only methods are distinguishable.

Example after a repository has been selected and cloned at a known commit:

```powershell
python .\src\extract_java_methods.py .\corpus\raw_repos\example `
  --repo-name owner/name `
  --repo-url https://github.com/owner/name `
  --commit-sha <40-character-commit-sha> `
  --output .\corpus\mined\example.methods.jsonl `
  --failures .\results\logs\example.extract-errors.jsonl
```

The command prints counts. Inspect several JSONL records and the failure log
manually before adding another repository. This pilot does not tokenize,
deduplicate, decontaminate, or claim the 300,000-instance target.

After manual review, run the repository eligibility audit:

```powershell
python .\src\audit_repository.py .\corpus\raw_repos\adobe-log-parser `
  --repo-name adobe/log-parser `
  --repo-url https://github.com/adobe/log-parser `
  --commit-sha 17043374da7906d5ecf27cc403e5cc5b86c78250 `
  --created 2021-01-26 `
  --contributors 8
```

The audit counts distinct source lines occupied by Tree-sitter comment nodes.
It applies the 30-line rule to the repository, while the extracted JSONL keeps
both commented and code-only methods. A nonzero exit code means at least one
eligibility criterion failed.

After the audit, deduplicate the pilot output:

```powershell
python .\src\deduplicate_methods.py `
  .\corpus\mined\adobe-log-parser.methods.jsonl `
  --output .\corpus\processed\adobe-log-parser.deduplicated.jsonl `
  --summary .\results\metrics\adobe-log-parser.deduplication.json
```

The deduplicator preserves the exact `code` and comment text, but uses a
whitespace-normalized comparison form. Its primary key is normalized method
code plus normalized comment role/kind/text. It also reports method-only
duplicates separately. Retained records contain SHA-256 comparison keys so
the comparison can be audited without storing another copy of normalized
source text.

Then decontaminate against both held-out splits of both assignment tasks:

```powershell
python .\src\decontaminate_methods.py `
  .\corpus\processed\adobe-log-parser.deduplicated.jsonl `
  --task-root . `
  --output .\corpus\processed\adobe-log-parser.decontaminated.jsonl `
  --summary .\results\metrics\adobe-log-parser.decontamination.json
```

This compares every normalized mined method and associated comment text with
every normalized validation/test source and target. It removes a record when
any one of those values overlaps and records the matching task and split in
the summary. The supplied TSV files are read-only inputs.

For `att/xacml-3.0`, the extraction produced 2,887 methods. Repository-local
deduplication retained 2,653 unique instances, and decontamination removed one
validation-source overlap, leaving 2,652 records. The removed record is
identified in the JSON summary; it was not silently discarded.

The two decontaminated repository outputs were then deduplicated globally. The
result contains 3,112 unique normalized method-plus-comment instances. There
were 91 duplicate normalized method-code records, but no duplicate full
instances across the two repositories because their associated comments
differed.

The initial two-repository estimate was superseded after processing four more
selected repositories. The six-repository global merge now contains 28,671
unique normalized instances from 28,674 decontaminated inputs. Three full
instances were duplicated across repositories, and there are 111 duplicate
method-code records.

After the selected Mapmaker parse-error policy was applied, the six-repository
global merge contains 28,609 unique normalized instances. The expanded
provisional length audit retained 27,884 of 28,609 instances (97.5%) under the
Java-like diagnostic. This gives a revised planning
estimate:

```text
provisional length-valid instances per repository = 27,884 / 6 = 4,647.3
repositories for 300,000 at that average = ceil(300,000 / 4,647.3) = 65 total
additional repositories beyond the current six = 59
```

This estimate is not a corpus-size result. It is based on six repositories,
uses a provisional tokenizer, and future repositories may have very different
yields. The 300,000 target remains unmet and unverified.

## Final ordered pre-tokenizer pipeline

On 2026-10-22, the ordered pipeline was rerun from all 21 mined JSONL files
using `src/build_corpus_pipeline.py`. It starts from raw extracted records,
then applies global exact deduplication, the approved near-deduplication
policy, the reviewed Mapmaker parse-error filter, and held-out
decontamination. The project tokenizer length filter is deliberately still
pending; the provisional lexical tokenizer is not used as final evidence.

The reproducible command was:

```powershell
python .\src\build_corpus_pipeline.py `
  --mined-dir .\corpus\mined `
  --task-root . `
  --output-dir .\corpus\processed\final_pipeline `
  --metrics .\results\metrics\final-corpus-pipeline.json `
  --parse-report .\results\metrics\hollow-cube-mapmaker.parse-errors.json
```

The count table reconciles at every completed stage:

| Stage | Before | Removed | After |
|---|---:|---:|---:|
| Extracted mined records | — | — | 256,123 |
| Exact whitespace-normalized deduplication | 256,123 | 69,015 | 187,108 |
| Near deduplication | 187,108 | 51,428 | 135,680 |
| Approved Mapmaker parse-error filter | 135,680 | 62 | 135,618 |
| Held-out decontamination | 135,618 | 8 | 135,610 |
| Project-tokenizer length filter | 135,610 | pending | pending |

Near-deduplication used ordered lexical-token `SequenceMatcher` similarity
with threshold 0.90 and a minimum of 10 combined method/comment tokens.
Records below that minimum were skipped for near-duplicate comparison (5,639
records in this run). The decontamination input contained 20,000 validation
and test rows across both tasks, and the eight removed records are listed in
the JSON metrics report.

The machine-readable evidence and outputs are:

- `results/metrics/final-corpus-pipeline.json`
- `corpus/processed/final_pipeline/final.exact-deduplicated.jsonl`
- `corpus/processed/final_pipeline/final.near-deduplicated.jsonl`
- `corpus/processed/final_pipeline/final.parse-filtered.jsonl`
- `corpus/processed/final_pipeline/final.decontaminated.jsonl`
- `corpus/processed/final_pipeline/final.near-deduplication-pairs.jsonl`

These 135,610 records are not yet the final usable corpus count because the
fresh tokenizer still must be trained and used to apply the assignment's
10--512-token rule.

## Fresh tokenizer and actual length filtering

The fresh tokenizer was trained only from
`corpus/processed/final_pipeline/final.decontaminated.jsonl` with:

- SentencePiece Unigram
- Vocabulary size 32,128
- Identity normalization
- 100 T5 sentinel tokens (`<extra_id_0>` through `<extra_id_99>`)
- `<START>` and `<END>` user-defined symbols
- Seed recorded as 680 in the tokenizer metadata

The training command was:

```powershell
python .\src\train_tokenizer.py `
  .\corpus\processed\final_pipeline\final.decontaminated.jsonl `
  --output-dir .\tokenizer\java_review_unigram `
  --vocab-size 32128 `
  --seed 680
```

The actual tokenizer audit command was:

```powershell
python .\src\audit_project_tokenizer.py `
  .\corpus\processed\final_pipeline\final.decontaminated.jsonl `
  --tokenizer .\tokenizer\java_review_unigram\java_review_unigram.model `
  --task-root . `
  --output .\corpus\processed\final_pipeline\final.tokenizer-valid.jsonl `
  --summary .\results\metrics\final-tokenizer-lengths.json
```

The final count table now reconciles through the real tokenizer:

| Stage | Before | Removed | After |
|---|---:|---:|---:|
| Extracted mined records | — | — | 256,123 |
| Exact whitespace-normalized deduplication | 256,123 | 69,015 | 187,108 |
| Near deduplication | 187,108 | 51,428 | 135,680 |
| Approved Mapmaker parse-error filter | 135,680 | 62 | 135,618 |
| Held-out decontamination | 135,618 | 8 | 135,610 |
| SentencePiece length filter, 10--512 tokens | 135,610 | 7,876 | **127,734** |

The 127,734 records are the current final usable mined-corpus count. The
300,000-instance target has not been met.

For the mined corpus, method-plus-comment documents had a mean length of
145.06 tokens, median 68, 90th percentile 315, and 95th percentile 475.
5,906 records (4.3551%) were longer than 512 tokens, and 1,970 (1.4525%) were
shorter than 10 tokens. Code-only lengths were also recorded in
`results/metrics/final-tokenizer-lengths.json`.

The task audit reports the required handling evidence for every train,
validation, and test split. The supplied TSV files were read only; no rows
were filtered or rewritten. For example, the training split had 4.01% of
`code&comment2code:` inputs and 0.88% of revised-code targets longer than
512 tokens. The `code2comment:` training split had 0.94% of inputs and
0.002% of targets longer than 512 tokens. All exact per-split distributions,
including shorter-than-10 fractions, are in the machine-readable report.

Tokenizer artifacts:

- `tokenizer/java_review_unigram/java_review_unigram.model`
- `tokenizer/java_review_unigram/java_review_unigram.vocab`
- `tokenizer/java_review_unigram/tokenizer_metadata.json`
- `results/metrics/final-tokenizer-lengths.json`
- `corpus/processed/final_pipeline/final.tokenizer-valid.jsonl`

## Second repository batch

The next 13 selected repositories were processed from verified pinned commits
on 2026-10-22. `hazendaz/jmockit1` was recorded as pending because no commit
SHA was supplied and was not processed. One Git transport issue occurred for
`cgjennings/strange-eons`; the supplied SHA was verified as the repository
`main` HEAD through the GitHub API and remote refs, then fetched through
`refs/heads/main` without changing the pinned commit.

The extractor's tree walk was changed from recursive to iterative after
`cardillan/mindcode` exposed a recursion-depth failure in a deeply nested
syntax tree. The fix was regression-tested. `assert-kth/flacoco` had one
unreadable non-UTF-8 Java file, which was recorded in its extraction failure
log rather than silently discarded. Parse-error review was performed for all
new repositories with parser errors; only directly affected methods were
removed.

The second ordered pipeline command was:

```powershell
python .\src\build_corpus_pipeline.py `
  --mined-dir .\corpus\mined `
  --task-root . `
  --output-dir .\corpus\processed\final_pipeline_batch2 `
  --metrics .\results\metrics\final-corpus-pipeline-batch2.json `
  --parse-report .\results\metrics\hollow-cube-mapmaker.parse-errors.json `
  --parse-report .\results\metrics\aliyun-alibabacloud-landing-zone.parse-errors.json `
  --parse-report .\results\metrics\cardillan-mindcode.parse-errors.json `
  --parse-report .\results\metrics\coolcrabs-brachyura.parse-errors.json `
  --parse-report .\results\metrics\e2wugui-zeze.parse-errors.json `
  --parse-report .\results\metrics\markusamshove-natls.parse-errors.json
```

The expanded count table is:

| Stage | Before | Removed | After |
|---|---:|---:|---:|
| Extracted mined records | — | — | 383,009 |
| Exact whitespace-normalized deduplication | 383,009 | 87,210 | 295,799 |
| Near deduplication | 295,799 | 72,649 | 223,150 |
| Approved parse-error filters | 223,150 | 69 | 223,081 |
| Held-out decontamination | 223,081 | 8 | 223,073 |
| SentencePiece length filter, 10--512 tokens | 223,073 | 14,103 | **208,970** |

The expanded tokenizer was retrained only on the 223,073-record expanded
decontaminated corpus, using the same 32,128-piece SentencePiece Unigram
configuration. Its length report is
`results/metrics/final-tokenizer-lengths-batch2.json`, and the usable corpus is
`corpus/processed/final_pipeline_batch2/final.tokenizer-valid.jsonl`.

The 208,970 usable records are below the 300,000 target by 91,030 records.
Across the 34 processed repositories, the observed planning rate is
approximately 6,146 usable records per repository. A simple estimate is about
49 total repositories, or 15 additional repositories, but this is not a
guarantee because repository yields and cross-repository duplication vary.

## Parse-error review

For `hollow-cube/mapmaker`, the parser-review report is:

```powershell
python .\src\review_parse_errors.py `
  .\corpus\raw_repos\hollow-cube-mapmaker `
  --output .\results\metrics\hollow-cube-mapmaker.parse-errors.json
```

The review distinguishes methods whose source range directly contains a
Tree-sitter `ERROR` node from methods in the same file but outside an error
range. This matters because a file-level parse error does not automatically
invalidate every method in that file.

The selected policy is to exclude only methods directly overlapping a reviewed
error node. The 364 methods outside error ranges remain eligible, while the 62
directly affected methods are removed before Mapmaker deduplication and
decontamination. The exact filter retained 10,980 of Mapmaker's 11,042
extracted records.

Because the project tokenizer has not been trained yet, length filtering first
uses the diagnostic script below. It is explicitly marked provisional and
counts method-plus-comment documents with a deterministic Java-like lexical
tokenizer:

```powershell
python .\src\audit_token_lengths.py `
  .\corpus\processed\global.deduplicated.jsonl `
  --output .\corpus\processed\global.provisional-token-valid.jsonl `
  --summary .\results\metrics\global.provisional-token-lengths.json
```

The report also gives code-only lengths for comparison. These counts must not
be presented as final tokenizer counts. After the project tokenizer is trained,
the same records must be measured again under that tokenizer.

The provisional report retained 2,848 of 3,112 instances (91.5%) using the
method-plus-comment length. For planning only, that is 1,424 provisional
length-valid instances per repository, implying:

```text
ceil(300,000 / 1,424) = 211 total repositories
211 - 2 processed repositories = 209 additional repositories
```

This replaces the earlier 193-repository estimate only for provisional
planning. The final estimate must use counts from the trained project
tokenizer.

## Ten-repository update

The next four confirmed repositories were processed without extraction
failures or parse-error files:

| Repository | Extracted methods | Local unique instances | Decontaminated instances |
|---|---:|---:|---:|
| `nativejdb/nativejdb` | 29,700 | 28,597 | 28,593 |
| `microsoft/reliableAI` | 2,917 | 2,665 | 2,665 |
| `MagicLibStarsector/MagicLib` | 1,173 | 942 | 942 |
| `mercari/pipeline` | 4,593 | 4,202 | 4,202 |

The four repositories contributed 36,402 records after local processing.
`nativejdb/nativejdb` had four overlaps with held-out targets from
`code-and-comment-to-code/test`; the other three repositories had no
decontamination removals.

The global merge now combines ten repositories and 65,014 decontaminated
inputs. It retains 64,975 unique normalized method-plus-comment instances,
with 39 duplicate full-instance records across repositories and 64,217 unique
normalized method-code values.

The provisional Java-like lexical audit retains 61,439 of 64,975 records
(94.6%) in the 10--512 range. This is still not the assignment's final
token-length result because the project tokenizer has not been trained. For
planning only:

```text
provisional length-valid instances per repository = 61,439 / 10 = 6,143.9
repositories for 300,000 at that average = ceil(300,000 / 6,143.9) = 49 total
additional repositories beyond the current ten = 39
```

This estimate is more current than the six-repository estimate but remains
unstable because it is based on only ten repositories and a provisional
tokenizer. It must be replaced after training and applying the actual project
tokenizer.

## Six-repository high-volume update

The six repositories selected with thresholds of at least 1,000 comment lines
and at least 50,000 nonblank, non-comment Java source lines all passed local
eligibility audits. The code-line measure excludes blank lines and
comment-only lines; lines containing both code and a trailing comment count as
code lines.

| Repository | Java files | Code lines | Comment lines | Methods extracted | Decontaminated instances |
|---|---:|---:|---:|---:|---:|
| `alibaba/cost-based-incremental-optimizer` | 1,879 | 299,111 | 112,286 | 23,478 | 22,273 |
| `binance/binance-connector-java` | 3,838 | 927,005 | 254,201 | 79,134 | 43,071 |
| `gmap/dspbench` | 933 | 51,585 | 9,990 | 4,161 | 2,269 |
| `nervenetwork/nerve` | 2,874 | 333,913 | 103,843 | 26,414 | 16,987 |
| `omnilaboratory/obandroid` | 663 | 73,244 | 22,868 | 6,781 | 6,122 |
| `zencodelang/zencode` | 943 | 70,621 | 4,007 | 6,731 | 5,989 |

The six repositories produced 147,699 extracted methods. Repository-local
exact deduplication and decontamination left 96,711 instances; seven records
were removed by decontamination (six Alibaba records and one Nerve record).
The global sixteen-repository merge contains 161,448 unique normalized
instances from 161,725 decontaminated inputs, removing 277 duplicate full
instances across repositories.

The provisional Java-like length audit retains 153,711 of 161,448 records
(95.2%) within 10--512 tokens. This is not the final tokenizer result. At the
current provisional average:

```text
153,711 / 16 = 9,606.9 provisional length-valid instances per repository
ceil(300,000 / 9,606.9) = 32 total repositories
additional repositories beyond the current sixteen = 16
```

The estimate remains provisional until the fresh tokenizer is trained and
applied.

## Five-repository update

Five additional repositories were successfully resolved to full commit SHAs,
audited under the high-volume thresholds, extracted, deduplicated, and
decontaminated. The supplied Create commit `e882a9ce` could not be resolved in
the repository, remote refs, or GitHub commit API, so that candidate was
excluded without substituting another snapshot.

| Repository | Java files | Code lines | Comment lines | Methods extracted | Decontaminated instances |
|---|---:|---:|---:|---:|---:|
| `the3deer/android-3D-engine` | 533 | 55,445 | 32,609 | 4,515 | 4,167 |
| `UltiKits/UltiTools-Reborn` | 528 | 79,171 | 20,555 | 7,233 | 6,956 |
| `cannolicatfish/project-rankine` | 690 | 63,010 | 3,728 | 3,825 | 2,910 |
| `javadev/leetcode-in-java` | 6,156 | 175,339 | 10,039 | 13,515 | 13,386 |
| `nemproject/nem` | 1,624 | 111,100 | 40,273 | 11,946 | 11,631 |

The five repositories produced 41,034 extracted methods. Local exact
deduplication and decontamination retained 39,050 records. Five records were
removed by decontamination: four from the 3D engine and one from Rankine.

The global merge now combines 21 included repositories and 200,775
decontaminated inputs. It retains 187,029 unique normalized
method-plus-comment instances, removing 13,746 duplicate full instances
across repositories. The duplicate increase is primarily due to
`javadev/leetcode-in-java` matching the earlier `LeetCode-in-Java` corpus
output; the two inputs each contributed 13,386 local records, but those
records are retained only once globally.

The provisional Java-like length audit retains 178,424 of 187,029 records
(95.4%) within 10--512 tokens. This is not the final tokenizer result. For
planning only:

```text
provisional length-valid instances per repository = 178,424 / 21 = 8,496.4
repositories for 300,000 at that average = ceil(300,000 / 8,496.4) = 36 total
additional repositories beyond the current twenty-one = 15
```

The estimate remains provisional until near-duplicate filtering and the fresh
project tokenizer are implemented and applied.

## Near-duplicate diagnostic

The selected near-duplicate policy is a conservative 0.90
`SequenceMatcher` similarity over ordered lexical tokens formed from each
method and its associated comments. Records shorter than 10 combined tokens
are not considered for near-duplicate removal, protecting short methods whose
generic tokens can hide meaningful message or operation differences. A
MinHash/LSH index generates candidate pairs, and every candidate is then
verified with exact ordered-token similarity. The original source and
comments are preserved; one deterministic representative is retained for each
detected near-duplicate relation.

Applied to the current 187,029-record global exact-deduplicated corpus, the
revised diagnostic examined 39,906,622 candidate pairs, skipped 5,639
short records, and removed 51,416 near-duplicate records across 17,632
groups. No exact duplicates were present in this input because exact
deduplication had already run. The output contains 135,613 records.

The provisional length audit of the revised near-deduplicated output retains
127,620 of 135,613 records (94.1%) in the 10--512 range. For planning only:

```text
provisional length-valid instances per repository = 127,620 / 21 = 6,077.1
repositories for 300,000 at that average = ceil(300,000 / 6,077.1) = 50 total
additional repositories beyond the current twenty-one = 29
```

This is a diagnostic on an already decontaminated corpus. The rubric requires
near-duplicate removal before other filters, so the final pipeline must rerun
near deduplication from the mined records before decontamination and tokenizer
length filtering, then produce a reconciled count table.
