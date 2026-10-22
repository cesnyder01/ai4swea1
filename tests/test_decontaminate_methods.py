import json

from src.decontaminate_methods import run


def test_removes_code_or_comment_overlaps_from_union_of_held_out_data(tmp_path):
    task_root = tmp_path / "tasks"
    (task_root / "code-and-comment-to-code").mkdir(parents=True)
    (task_root / "code-to-comment").mkdir(parents=True)
    for task in ("code-and-comment-to-code", "code-to-comment"):
        for split in ("val", "test"):
            (task_root / task / f"{split}.tsv").write_text(
                " held out code \t held out target \n", encoding="utf-8"
            )
    source = tmp_path / "input.jsonl"
    records = [
        {
            "id": "remove-code",
            "code": "held   out code",
            "comments": [],
            "provenance": {},
        },
        {
            "id": "remove-comment",
            "code": "safe method",
            "comments": [{"text": "held out target"}],
            "provenance": {},
        },
        {"id": "keep", "code": "safe", "comments": [], "provenance": {}},
    ]
    source.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    output = tmp_path / "output.jsonl"
    summary = tmp_path / "summary.json"
    result = run(source, task_root, output, summary)

    assert result["input_records"] == 3
    assert result["held_out_rows"] == 4
    assert result["removed_records"] == 2
    assert result["retained_records"] == 1
    assert [json.loads(line)["id"] for line in output.read_text(encoding="utf-8").splitlines()] == [
        "keep"
    ]
