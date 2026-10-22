from src.near_deduplicate_methods import (
    jaccard,
    near_deduplicate,
    sequence_similarity,
    token_set,
)


def record(identifier: str, code: str) -> dict:
    return {
        "id": identifier,
        "code": code,
        "comments": [],
        "provenance": {
            "repository": "owner/repo",
            "file": f"{identifier}.java",
            "start_line": 1,
            "end_line": 3,
        },
    }


def test_jaccard_and_near_duplicate_removal_preserve_representative():
    left = record("a", "return alpha + beta + gamma + delta + epsilon + zeta + eta + theta;")
    right = record(
        "b",
        "return alpha + beta + gamma + delta + epsilon + zeta + eta + theta + zero;",
    )
    unrelated = record("c", "throw new IllegalStateException();")

    assert jaccard(token_set(left), token_set(right)) >= 0.90
    retained, summary, pairs = near_deduplicate([right, unrelated, left])

    assert [item["id"] for item in retained] == ["a", "c"]
    assert summary["near_duplicate_records_removed"] == 1
    assert summary["retained_records"] == 2
    assert pairs[0]["representative_id"] == "a"
    assert pairs[0]["removed_id"] == "b"


def test_short_methods_are_not_near_deduplicated():
    left = record("a", 'throw new UnsupportedOperationException("Not a valid annotation");')
    right = record("b", 'throw new UnsupportedOperationException("Not supported");')

    retained, summary, _ = near_deduplicate([left, right])

    assert len(retained) == 2
    assert summary["near_duplicate_records_removed"] == 0
    assert summary["short_records_skipped"] == 2


def test_sequence_similarity_preserves_token_order():
    assert sequence_similarity(("a", "b", "c"), ("a", "c", "b")) < 0.90
