import json

from src.extract_java_methods import run, walk


class FakeNode:
    def __init__(self, children=None):
        self.children = children or []


def test_walk_handles_deep_trees_without_recursion_error():
    root = FakeNode()
    current = root
    for _ in range(2000):
        child = FakeNode()
        current.children = [child]
        current = child

    assert len(list(walk(root))) == 2001


def test_extracts_methods_and_associates_adjacent_comments(tmp_path):
    repository = tmp_path / "repo"
    source = repository / "src" / "Demo.java"
    source.parent.mkdir(parents=True)
    source.write_text(
        "/** Adds values. */\nclass Demo {\n"
        "  // keep this note\n"
        "  int add(int left, int right) { return left + right; }\n"
        "  int plain() { return 1; }\n"
        "}\n",
        encoding="utf-8",
    )
    output = tmp_path / "methods.jsonl"

    stats = run(repository, output, "example/Demo", "https://github.com/example/Demo", "abc123")

    assert stats.files_seen == 1
    assert stats.methods_extracted == 2
    assert stats.methods_with_comments == 1
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert records[0]["has_comment"] is True
    assert records[0]["comments"] == [
        {"role": "preceding", "kind": "line_comment", "text": "// keep this note"}
    ]
    assert records[0]["provenance"]["commit_sha"] == "abc123"
    assert records[1]["has_comment"] is False
