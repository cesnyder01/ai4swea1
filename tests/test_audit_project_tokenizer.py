import json

from src.audit_project_tokenizer import run


def test_audit_uses_real_tokenizer_for_corpus_and_tasks(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {
                "id": "one",
                "code": "return value;",
                "comments": [{"text": "a comment"}],
                "provenance": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    tasks = tmp_path / "tasks"
    for task in ("code-and-comment-to-code", "code-to-comment"):
        directory = tasks / task
        directory.mkdir(parents=True)
        for split in ("train", "val", "test"):
            (directory / f"{split}.tsv").write_text(
                "return value;\tupdated value\n", encoding="utf-8"
            )

    from src.train_tokenizer import train

    tokenizer_dir = tmp_path / "tokenizer"
    train(corpus, tokenizer_dir, vocab_size=118)
    result = run(
        corpus,
        tokenizer_dir / "java_review_unigram.model",
        tasks,
        tmp_path / "valid.jsonl",
        tmp_path / "summary.json",
    )

    assert result["vocab_size"] == 118
    assert result["corpus"]["retained_records"] == 1
    assert result["tasks"]["code-to-comment"]["train"]["rows"] == 1
