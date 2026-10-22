import json

from src.build_corpus_pipeline import run


def record(identifier: str, code: str, file_name: str = "Example.java") -> dict:
    return {
        "id": identifier,
        "code": code,
        "comments": [],
        "provenance": {
            "repository": "owner/repo",
            "file": file_name,
            "start_line": 1,
            "end_line": 3,
        },
    }


def test_pipeline_orders_deduplication_before_filters(tmp_path):
    mined = tmp_path / "mined"
    mined.mkdir()
    records = [
        record("keep", "return alpha + beta + gamma + delta + epsilon + zeta;"),
        record(
            "near",
            "return alpha + beta + gamma + delta + epsilon + zeta + extra;",
        ),
        record("held-out", "held out code"),
    ]
    (mined / "repo.methods.jsonl").write_text(
        "\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8"
    )

    for task in ("code-and-comment-to-code", "code-to-comment"):
        for split in ("val", "test"):
            directory = tmp_path / "tasks" / task
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{split}.tsv").write_text(
                "held out code\ttarget\n", encoding="utf-8"
            )

    metrics = tmp_path / "metrics.json"
    summary = run(mined, tmp_path / "tasks", tmp_path / "processed", metrics)

    assert summary["stages"][1]["name"] == "exact_deduplication"
    assert summary["stages"][2]["name"] == "near_deduplication"
    assert summary["stages"][4]["name"] == "held_out_decontamination"
    assert summary["stages"][2]["records_after"] == 2
    assert summary["stages"][4]["removed_records"] == 1
    assert summary["stages"][5]["status"] == "pending_tokenizer_training"
