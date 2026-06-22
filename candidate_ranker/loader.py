"""Candidate data loading. Supports plain and gzipped JSONL."""

import gzip
import json
from typing import Iterator, List


def _open(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def iter_candidates(path: str) -> Iterator[dict]:
    with _open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_candidates(path: str) -> List[dict]:
    return list(iter_candidates(path))
