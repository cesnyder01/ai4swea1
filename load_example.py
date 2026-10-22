"""Minimal loader. Each TSV row is: source<TAB>target, no header, UTF-8, one instance per line.
Do not use csv.reader with default quoting: the code contains quotes. Split on the first tab only."""
from pathlib import Path

PREFIX = {"code-and-comment-to-code": "code&comment2code: ",
          "code-to-comment": "code2comment: "}

def task_file(root, task, split):
    candidates = (
        Path(root) / task / f"{split}.tsv",
        Path(root) / task / task / f"{split}.tsv",
    )
    for path in candidates:
        if path.is_file():
            return path
    expected = " or ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not find {task} {split} data; checked {expected}")

def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        for line in f:
            src, tgt = line.rstrip("\n").split("\t", 1)
            yield src, tgt

def load_task(root, task, split, with_prefix=True):
    for src, tgt in read_tsv(task_file(root, task, split)):
        yield (PREFIX[task] + src if with_prefix else src), tgt

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    for task in PREFIX:
        for split in ("train", "val", "test"):
            n = sum(1 for _ in load_task(root, task, split))
            print(f"{task:26s} {split:5s} {n:>7d}")
