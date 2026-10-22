"""Report Tree-sitter parse errors and methods directly affected by them."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from tree_sitter import Language, Parser
import tree_sitter_java

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.extract_java_methods import java_files, walk


def classify_line(line: str) -> str:
    if "case " in line and "->" in line:
        return "pattern-switch-case"
    if "catch (" in line and "_" in line:
        return "unnamed-catch-parameter"
    if "instanceof " in line and ("var" in line or "(" in line):
        return "pattern-matching-instanceof"
    if "switch (" in line:
        return "switch-expression"
    return "other"


def run(root: Path, output: Path) -> dict[str, Any]:
    parser = Parser()
    parser.language = Language(tree_sitter_java.language())
    files: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    error_nodes = 0
    affected_methods = 0
    unaffected_methods_in_error_files = 0
    for path in java_files(root):
        source = path.read_bytes()
        text = source.decode("utf-8", errors="replace")
        lines = text.splitlines()
        tree = parser.parse(source)
        errors = [node for node in walk(tree.root_node) if node.type == "ERROR"]
        if not errors:
            continue
        error_nodes += len(errors)
        error_details = []
        for error in errors:
            line = lines[error.start_point.row] if error.start_point.row < len(lines) else ""
            category = classify_line(line)
            category_counts[category] += 1
            error_details.append(
                {
                    "category": category,
                    "start_line": error.start_point.row + 1,
                    "end_line": error.end_point.row + 1,
                    "text": line.strip(),
                }
            )
        methods = [node for node in walk(tree.root_node) if node.type == "method_declaration"]
        affected = []
        for method in methods:
            if any(
                error.start_byte < method.end_byte and method.start_byte < error.end_byte
                for error in errors
            ):
                affected.append(
                    {
                        "start_line": method.start_point.row + 1,
                        "end_line": method.end_point.row + 1,
                    }
                )
        affected_methods += len(affected)
        unaffected_methods_in_error_files += len(methods) - len(affected)
        files.append(
            {
                "file": path.relative_to(root).as_posix(),
                "error_nodes": error_details,
                "methods_in_file": len(methods),
                "methods_containing_error": affected,
            }
        )
    report = {
        "repository": str(root),
        "parse_error_files": len(files),
        "error_nodes": error_nodes,
        "methods_in_error_files": affected_methods + unaffected_methods_in_error_files,
        "methods_containing_error": affected_methods,
        "methods_outside_error_nodes": unaffected_methods_in_error_files,
        "error_category_counts": dict(sorted(category_counts.items())),
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("repository", type=Path)
    arguments.add_argument("--output", type=Path, required=True)
    args = arguments.parse_args()
    if not args.repository.is_dir():
        print(f"Repository directory does not exist: {args.repository}", file=sys.stderr)
        return 2
    report = run(args.repository, args.output)
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
