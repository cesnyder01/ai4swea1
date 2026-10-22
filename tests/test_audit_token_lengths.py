import json

from src.audit_token_lengths import provisional_tokens, run


def test_provisional_tokenizer_is_deterministic_and_audit_is_explicit(tmp_path):
    assert provisional_tokens("return   value + 1;") == ["return", "value", "+", "1", ";"]
    source = tmp_path / "input.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "one",
                "code": "int value() { return 1; }",
                "comments": [{"text": "// small comment", "role": "preceding", "kind": "line_comment"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.jsonl"
    summary = tmp_path / "summary.json"

    result = run(source, output, summary)

    assert result["final_tokenizer"] is False
    assert result["input_records"] == 1
    assert result["provisional_retained_records"] == 1
