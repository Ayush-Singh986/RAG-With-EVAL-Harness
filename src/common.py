import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
RERANK_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
PREFIX = "Represent this sentence for searching relevant passages: "


def read(file: str) -> str:
    path = (CLEAN / file).resolve()
    if path.parent != CLEAN.resolve():
        raise ValueError(f"Document path must be a file directly under {CLEAN}")
    return path.read_text(encoding="utf-8")


def load_json(path: str | pathlib.Path) -> Any:
    target = pathlib.Path(path)
    if not target.is_absolute():
        target = ROOT / target
    with target.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | pathlib.Path, value: Any) -> None:
    target = pathlib.Path(path)
    if not target.is_absolute():
        target = ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
