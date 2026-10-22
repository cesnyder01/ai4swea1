import json

from src.filter_parse_error_methods import run


def test_filters_only_methods_overlapping_reviewed_errors(tmp_path):
    source = tmp_path / "input.jsonl"
    records = [
        {
            "id": "bad",
            "code": "bad",
            "comments": [],
            "provenance": {"file": "Example.java", "start_line": 10, "end_line": 15},
        },
        {
            "id": "good",
            "code": "good",
            "comments": [],
            "provenance": {"file": "Example.java", "start_line": 20, "end_line": 25},
        },
    ]
    source.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "file": "Example.java",
                        "methods_containing_error": [{"start_line": 10, "end_line": 15}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "output.jsonl"
    summary = tmp_path / "summary.json"

    result = run(source, report, output, summary)

    assert result == {
        "input_records": 2,
        "removed_records": 1,
        "retained_records": 1,
        "reviewed_affected_methods": 1,
    }
    assert json.loads(output.read_text(encoding="utf-8"))["id"] == "good"
