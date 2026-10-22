import json

from src.train_tokenizer import SENTINEL_TOKENS, train


def test_train_tokenizer_adds_assignment_symbols(tmp_path):
    source = tmp_path / "corpus.jsonl"
    record = {
        "id": "one",
        "code": "return value;",
        "comments": [{"text": "Explain <START> this <END>."}],
        "provenance": {},
    }
    source.write_text(json.dumps(record) + "\n", encoding="utf-8")

    metadata = train(source, tmp_path / "tokenizer", vocab_size=122)

    assert metadata["tokenizer_type"] == "SentencePiece Unigram"
    assert metadata["training_records"] == 1
    assert metadata["vocab_size"] == 122
    assert metadata["special_tokens"]["user_defined"][:2] == ["<START>", "<END>"]
    assert metadata["special_tokens"]["user_defined"][2:] == list(SENTINEL_TOKENS)
