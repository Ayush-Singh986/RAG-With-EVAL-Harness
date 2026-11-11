import argparse
import json

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from chunkers import CHUNKERS, build_chunks
from common import MODEL_NAME, ROOT

CACHE = ROOT / ".cache"


def embed_text(chunk: dict, add_title: bool) -> str:
    return f"{chunk['title']}\n{chunk['text']}" if add_title else chunk["text"]


def build_index(
    name: str, model: SentenceTransformer, add_title: bool = False
) -> int:
    chunks = build_chunks(name, model)
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / f"chunks_{name}.json").open("w", encoding="utf-8") as handle:
        json.dump(chunks, handle, ensure_ascii=False)
    collection_name = f"{name}_{'t' if add_title else 'p'}"
    vectors = []
    for start in tqdm(
        range(0, len(chunks), 1000), desc=f"Embedding {name}", unit="batch"
    ):
        batch = chunks[start:start + 1000]
        embeddings = model.encode(
            [embed_text(chunk, add_title) for chunk in batch],
            batch_size=64,
            normalize_embeddings=True,
        )
        vectors.append(np.asarray(embeddings, dtype=np.float32))
    np.savez_compressed(
        CACHE / f"vectors_{collection_name}.npz",
        embeddings=np.concatenate(vectors, axis=0),
    )
    print(f"{name} indexed {len(chunks)} chunks ({collection_name})")
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--add-title", action="store_true",
        help="Build title-prefixed indexes as a separate experiment",
    )
    parser.add_argument("--chunker", choices=CHUNKERS)
    args = parser.parse_args()
    if not any((ROOT / "data" / "clean").glob("*.md")):
        raise FileNotFoundError("No cleaned documents; run `make data` first")
    model = SentenceTransformer(MODEL_NAME)
    names = [args.chunker] if args.chunker else CHUNKERS
    for name in names:
        build_index(name, model, add_title=args.add_title)


if __name__ == "__main__":
    main()
