"""Extract Java methods and nearby comments into provenance-rich JSONL.

This is a pilot extractor, not a claim that the assignment corpus target is met.
It deliberately keeps source text intact and records failures instead of silently
dropping files.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

from tree_sitter import Language, Node, Parser
import tree_sitter_java


SKIP_DIRECTORIES = {
    ".git",
    ".gradle",
    ".idea",
    ".mvn",
    "build",
    "dist",
    "generated",
    "node_modules",
    "target",
    "vendor",
}
COMMENT_TYPES = {"block_comment", "line_comment"}


@dataclass
class ExtractionStats:
    files_seen: int = 0
    files_parsed: int = 0
    files_with_parse_errors: int = 0
    methods_extracted: int = 0
    methods_with_comments: int = 0
    code_only_methods: int = 0
    failures: int = 0


def parser() -> Parser:
    result = Parser()
    result.language = Language(tree_sitter_java.language())
    return result


def java_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.java")):
        if not any(part in SKIP_DIRECTORIES for part in path.parts):
            yield path


def walk(node: Node) -> Iterator[Node]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def comment_text(comment: Node, source: bytes) -> str:
    return source[comment.start_byte:comment.end_byte].decode("utf-8").rstrip("\r\n")


def comments_for_method(method: Node, source: bytes) -> list[dict[str, object]]:
    comments: list[dict[str, object]] = []
    parent = method.parent
    if parent is not None:
        siblings = parent.children
        index = siblings.index(method)
        preceding: list[Node] = []
        for sibling in reversed(siblings[:index]):
            if sibling.type not in COMMENT_TYPES:
                break
            preceding.append(sibling)
        for comment in reversed(preceding):
            comments.append(
                {
                    "role": "preceding",
                    "kind": comment.type,
                    "text": comment_text(comment, source),
                }
            )
    for node in walk(method):
        if node.type in COMMENT_TYPES:
            comments.append(
                {
                    "role": "inside",
                    "kind": node.type,
                    "text": comment_text(node, source),
                }
            )
    return comments


def extract_file(path: Path, root: Path, parser_instance: Parser, repo_name: str,
                 repo_url: str, commit_sha: str) -> tuple[list[dict[str, object]], bool]:
    source = path.read_bytes()
    tree = parser_instance.parse(source)
    methods = [node for node in walk(tree.root_node) if node.type == "method_declaration"]
    records = []
    for index, method in enumerate(methods):
        comments = comments_for_method(method, source)
        records.append(
            {
                "id": f"{path.relative_to(root).as_posix()}#method-{index}",
                "code": source[method.start_byte:method.end_byte].decode("utf-8"),
                "comments": comments,
                "has_comment": bool(comments),
                "provenance": {
                    "repository": repo_name,
                    "repository_url": repo_url,
                    "commit_sha": commit_sha,
                    "file": path.relative_to(root).as_posix(),
                    "start_line": method.start_point.row + 1,
                    "end_line": method.end_point.row + 1,
                },
            }
        )
    return records, tree.root_node.has_error


def run(root: Path, output: Path, repo_name: str, repo_url: str, commit_sha: str,
        failures_path: Path | None = None) -> ExtractionStats:
    stats = ExtractionStats()
    errors: list[dict[str, str]] = []
    parser_instance = parser()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as destination:
        for path in java_files(root):
            stats.files_seen += 1
            try:
                records, parse_error = extract_file(
                    path, root, parser_instance, repo_name, repo_url, commit_sha
                )
                stats.files_parsed += 1
                stats.files_with_parse_errors += int(parse_error)
                for record in records:
                    destination.write(json.dumps(record, ensure_ascii=True) + "\n")
                stats.methods_extracted += len(records)
                stats.methods_with_comments += sum(bool(record["has_comment"]) for record in records)
                stats.code_only_methods += sum(not record["has_comment"] for record in records)
            except (OSError, UnicodeDecodeError) as exc:
                stats.failures += 1
                errors.append({"file": path.as_posix(), "error": str(exc)})
    if failures_path is not None:
        failures_path.parent.mkdir(parents=True, exist_ok=True)
        failures_path.write_text(
            "\n".join(json.dumps(error, ensure_ascii=True) for error in errors) + (
                "\n" if errors else ""
            ),
            encoding="utf-8",
        )
    return stats


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("repository", type=Path)
    arguments.add_argument("--output", type=Path, required=True)
    arguments.add_argument("--failures", type=Path)
    arguments.add_argument("--repo-name", required=True)
    arguments.add_argument("--repo-url", required=True)
    arguments.add_argument("--commit-sha", required=True)
    args = arguments.parse_args()
    if not args.repository.is_dir():
        print(f"Repository directory does not exist: {args.repository}", file=sys.stderr)
        return 2
    stats = run(
        args.repository,
        args.output,
        args.repo_name,
        args.repo_url,
        args.commit_sha,
        args.failures,
    )
    print(json.dumps(asdict(stats), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
