import json

from src.audit_repository import audit


def test_audit_reports_each_repository_criterion(tmp_path):
    (tmp_path / "LICENSE").write_text(
        "Permission is hereby granted for the Software, without restriction.\n"
        "THE SOFTWARE IS PROVIDED AS IS.\n",
        encoding="utf-8",
    )
    source = tmp_path / "Example.java"
    source.write_text(
        "/** one\n * two\n */\nclass Example {\n"
        "  // three\n"
        "  int value() { return 1; }\n"
        "}\n",
        encoding="utf-8",
    )

    result = audit(tmp_path, "owner/Example", "https://github.com/owner/Example", "abc", "2021-01-26", 8)

    assert result.mit_license_found is True
    assert result.java_files == 1
    assert result.comment_lines == 4
    assert result.code_lines == 3
    assert result.code_line_threshold_met is True
    assert result.eligible is False
    assert json.loads(json.dumps(result.__dict__))["license_file"] == "LICENSE"
