import json

from src.merge_deduplicate_methods import run


def make_record(identifier: str, repository: str) -> dict:
    return {
        "id": identifier,
        "code": "return 1;",
        "comments": [],
        "provenance": {
            "repository": repository,
            "file": f"{identifier}.java",
            "start_line": 1,
            "end_line": 1,
        },
    }


def test_global_deduplication_reports_cross_repository_duplicates(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first.write_text(json.dumps(make_record("a", "owner/first")) + "\n", encoding="utf-8")
    second.write_text(json.dumps(make_record("b", "owner/second")) + "\n", encoding="utf-8")
    output = tmp_path / "merged.jsonl"
    summary = tmp_path / "summary.json"

    result = run([first, second], output, summary)

    assert result["input_records"] == 2
    assert result["unique_normalized_instances"] == 1
    assert result["duplicate_instance_records"] == 1
    assert result["cross_repository_duplicate_records"] == 1
    assert (output.read_text(encoding="utf-8").count("\n")) == 1
