"""Audit one selected Java repository against the assignment's eligibility rules."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tree_sitter import Language, Parser
import tree_sitter_java

from src.extract_java_methods import COMMENT_TYPES, java_files, walk


@dataclass
class AuditResult:
    repository: str
    repository_url: str
    commit_sha: str
    created: str
    contributors: int
    java_files: int
    comment_lines: int
    code_lines: int
    mit_license_found: bool
    created_in_range: bool
    contributor_count_in_range: bool
    has_java_source: bool
    comment_threshold_met: bool
    code_line_threshold_met: bool
    eligible: bool
    license_file: str | None


def parser() -> Parser:
    result = Parser()
    result.language = Language(tree_sitter_java.language())
    return result


def comment_line_count(path: Path, parser_instance: Parser) -> int:
    source = path.read_bytes()
    tree = parser_instance.parse(source)
    lines: set[int] = set()
    for node in walk(tree.root_node):
        if node.type in COMMENT_TYPES:
            lines.update(range(node.start_point.row, node.end_point.row + 1))
    return len(lines)


def code_line_count(path: Path, parser_instance: Parser) -> int:
    source = path.read_bytes()
    tree = parser_instance.parse(source)
    comment_rows: set[int] = set()
    for node in walk(tree.root_node):
        if node.type in COMMENT_TYPES:
            comment_rows.update(range(node.start_point.row, node.end_point.row + 1))
    return sum(
        1
        for row, line in enumerate(source.decode("utf-8", errors="replace").splitlines())
        if line.strip() and (row not in comment_rows or not line.lstrip().startswith(("//", "/*", "*", "*/")))
    )


def find_mit_license(root: Path) -> Path | None:
    candidates = [
        path
        for path in root.iterdir()
        if path.is_file() and path.name.lower() in {"license", "license.txt", "license.md"}
    ]
    for path in sorted(candidates):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        is_mit = "mit license" in text or (
            "permission is hereby granted" in text
            and "the software is provided" in text
            and "without restriction" in text
        )
        if is_mit:
            return path
    return None


def audit(root: Path, repository: str, repository_url: str, commit_sha: str,
          created: str, contributors: int, min_comment_lines: int = 30,
          min_code_lines: int = 0) -> AuditResult:
    created_date = date.fromisoformat(created)
    parser_instance = parser()
    files = list(java_files(root))
    comment_lines = sum(comment_line_count(path, parser_instance) for path in files)
    code_lines = sum(code_line_count(path, parser_instance) for path in files)
    license_path = find_mit_license(root)
    created_in_range = date(2020, 1, 1) <= created_date <= date(2022, 12, 31)
    contributor_count_in_range = 3 <= contributors <= 15
    result = AuditResult(
        repository=repository,
        repository_url=repository_url,
        commit_sha=commit_sha,
        created=created,
        contributors=contributors,
        java_files=len(files),
        comment_lines=comment_lines,
        code_lines=code_lines,
        mit_license_found=license_path is not None,
        created_in_range=created_in_range,
        contributor_count_in_range=contributor_count_in_range,
        has_java_source=bool(files),
        comment_threshold_met=comment_lines >= min_comment_lines,
        code_line_threshold_met=code_lines >= min_code_lines,
        eligible=False,
        license_file=str(license_path.relative_to(root)) if license_path else None,
    )
    result.eligible = all(
        (
            result.mit_license_found,
            result.created_in_range,
            result.contributor_count_in_range,
            result.has_java_source,
            result.comment_threshold_met,
            result.code_line_threshold_met,
        )
    )
    return result


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("repository", type=Path)
    arguments.add_argument("--repo-name", required=True)
    arguments.add_argument("--repo-url", required=True)
    arguments.add_argument("--commit-sha", required=True)
    arguments.add_argument("--created", required=True)
    arguments.add_argument("--contributors", type=int, required=True)
    arguments.add_argument("--min-comment-lines", type=int, default=30)
    arguments.add_argument("--min-code-lines", type=int, default=0)
    args = arguments.parse_args()
    if not args.repository.is_dir():
        print(f"Repository directory does not exist: {args.repository}", file=sys.stderr)
        return 2
    result = audit(
        args.repository,
        args.repo_name,
        args.repo_url,
        args.commit_sha,
        args.created,
        args.contributors,
        args.min_comment_lines,
        args.min_code_lines,
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 0 if result.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
