import json

from src.review_parse_errors import classify_line, run


def test_classifies_modern_java_syntax():
    assert classify_line("case Value(var item) ->") == "pattern-switch-case"
    assert classify_line("catch (Exception _) {}") == "unnamed-catch-parameter"
    assert classify_line("if (value instanceof Result.Ok(var item))") == "pattern-matching-instanceof"


def test_parse_error_report_has_explicit_method_groups(tmp_path):
    source = tmp_path / "Example.java"
    source.write_text(
        "class Example { int value() { return 1; } }\n",
        encoding="utf-8",
    )
    output = tmp_path / "parse-errors.json"

    report = run(tmp_path, output)

    assert report["parse_error_files"] == 0
    assert report["methods_containing_error"] == 0
    assert json.loads(output.read_text(encoding="utf-8"))["error_nodes"] == 0
