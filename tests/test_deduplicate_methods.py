import json

from src.deduplicate_methods import normalize_for_comparison, run


def record(identifier: str, code: str, comment: str) -> dict:
    return {
        "id": identifier,
        "code": code,
        "comments": [{"role": "preceding", "kind": "line_comment", "text": comment}],
        "provenance": {
            "repository": "owner/repo",
            "file": f"{identifier}.java",
            "start_line": 1,
            "end_line": 2,
        },
    }


def test_normalization_and_deduplication_preserve_exact_source(tmp_path):
    assert normalize_for_comparison("  return   1;\r\n") == "return 1;"
    source = tmp_path / "methods.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps(record("a", "return  1;", "// note")),
                json.dumps(record("b", "return 1;", "// note")),
                json.dumps(record("c", "return 1;", "// other")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "deduplicated.jsonl"
    summary = tmp_path / "summary.json"

    result = run(source, output, summary)

    assert result == {
        "input_records": 3,
        "unique_normalized_methods": 1,
        "duplicate_method_records": 2,
        "unique_normalized_instances": 2,
        "duplicate_instance_records": 1,
        "malformed_records": 0,
    }
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert records[0]["code"] == "return  1;"
    assert "comparison" in records[0]
