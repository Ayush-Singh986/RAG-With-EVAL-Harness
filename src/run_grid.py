import itertools

import numpy as np
import pandas as pd
from sentence_transformers import CrossEncoder, SentenceTransformer

from chunkers import CHUNKERS
from common import MODEL_NAME, ROOT, RERANK_NAME, load_json
from metrics import run_setup
from retrievers import Retriever


def main() -> None:
    questions = load_json("data/testset_dev.json")
    model, reranker = SentenceTransformer(MODEL_NAME), CrossEncoder(RERANK_NAME)
    rows = []
    for chunker in CHUNKERS:
        ret = Retriever(chunker, model=model, reranker=reranker)
        average_chars = round(float(np.mean([len(chunk["text"]) for chunk in ret.chunks])))
        for search, rerank in itertools.product(
            ["vector", "bm25", "hybrid"], [False, True]
        ):
            aggregate, _ = run_setup(ret, questions, search, rerank)
            row = {
                "chunker": chunker, "search": search, "rerank": rerank,
                "avg_chunk_chars": average_chars, **aggregate,
            }
            rows.append(row)
            print(row)
    results = ROOT / "results"
    results.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(results / "grid.csv", index=False)
    print(f"Wrote {len(rows)} setups to {results / 'grid.csv'}")


if __name__ == "__main__":
    main()
