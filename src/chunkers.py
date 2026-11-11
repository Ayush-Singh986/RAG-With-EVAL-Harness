import re
from typing import Callable

import numpy as np

from common import CLEAN, ROOT, load_json

HEAD = re.compile(r"^#{1,4} .*$", re.M)


def fixed(text: str, size: int = 500, overlap: int = 50) -> list[tuple[int, int]]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    spans = []
    step = size - overlap
    for start in range(0, len(text), step):
        end = min(start + size, len(text))
        spans.append((start, end))
        if end == len(text):
            break
    return spans


def by_heading(text: str, max_len: int = 1000, min_len: int = 150) -> list[tuple[int, int]]:
    if max_len <= 0 or min_len < 0:
        raise ValueError("max_len must be positive and min_len non-negative")
    bounds = sorted({0, len(text), *(match.start() for match in HEAD.finditer(text))})
    spans: list[tuple[int, int]] = []
    for start, end in zip(bounds, bounds[1:]):
        if end - start <= max_len:
            spans.append((start, end))
        else:
            spans.extend((start + a, start + b) for a, b in fixed(text[start:end], max_len, 100))
    merged: list[tuple[int, int]] = []
    i = 0
    while i < len(spans):
        start, end = spans[i]
        while end - start < min_len and i + 1 < len(spans):
            i += 1
            end = spans[i][1]
        merged.append((start, end))
        i += 1
    return merged


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    start = 0
    for match in re.finditer(r"(?<=[.!?])\s+|\n{2,}", text):
        if match.start() > start:
            spans.append((start, match.start()))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def semantic(
    text: str, model: object, pct: float = 10, min_len: int = 200, max_len: int = 1000
) -> list[tuple[int, int]]:
    if not 0 <= pct <= 100 or min_len < 0 or max_len <= 0:
        raise ValueError("Invalid semantic chunking parameters")
    spans = sentence_spans(text)
    if len(spans) < 2:
        return [(0, len(text))] if text else []
    embeddings = model.encode(
        [text[start:end] for start, end in spans], normalize_embeddings=True
    )
    similarities = (embeddings[:-1] * embeddings[1:]).sum(axis=1)
    threshold = np.percentile(similarities, pct)
    chunks = []
    start = spans[0][0]
    for i in range(1, len(spans)):
        current_len = spans[i - 1][1] - start
        too_big = spans[i][1] - start > max_len
        topic_change = similarities[i - 1] < threshold and current_len >= min_len
        if topic_change or too_big:
            chunks.append((start, spans[i - 1][1]))
            start = spans[i][0]
    chunks.append((start, spans[-1][1]))
    return chunks


CHUNKERS: dict[str, Callable] = {
    "fixed500": lambda text, model: fixed(text, 500, 50),
    "fixed1000": lambda text, model: fixed(text, 1000, 100),
    "heading": lambda text, model: by_heading(text),
    "semantic": lambda text, model: semantic(text, model),
}


def build_chunks(name: str, model: object | None = None) -> list[dict]:
    if name not in CHUNKERS:
        raise ValueError(f"Unknown chunker {name!r}; choose from {', '.join(CHUNKERS)}")
    if name == "semantic" and model is None:
        raise ValueError("The semantic chunker requires an embedding model")
    titles = load_json("data/titles.json")
    output = []
    for path in sorted(CLEAN.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for start, end in CHUNKERS[name](text, model):
            if end - start < 30:
                continue
            output.append({
                "id": f"{path.name}:{start}", "file": path.name, "start": start,
                "end": end, "text": text[start:end], "title": titles.get(path.name, ""),
            })
    if not output:
        raise RuntimeError(f"No chunks built from {CLEAN}; run the data pipeline first")
    return output
