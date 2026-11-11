from __future__ import annotations

import numpy as np

from common import MODEL_NAME, PREFIX, RERANK_NAME, ROOT, load_json, tokenize

SEARCH_TYPES = {"vector", "bm25", "hybrid"}


def rrf(lists: list[list[str]], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranked in lists:
        for rank, chunk_id in enumerate(ranked):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)


class Retriever:
    def __init__(
        self,
        chunker: str,
        add_title: bool = False,
        model: SentenceTransformer | None = None,
        reranker: CrossEncoder | None = None,
        use_prefix: bool = True,
    ):
        from rank_bm25 import BM25Okapi
        from sentence_transformers import CrossEncoder, SentenceTransformer

        self.model = model or SentenceTransformer(MODEL_NAME)
        self.reranker = reranker or CrossEncoder(RERANK_NAME)
        self.use_prefix = use_prefix
        chunk_path = ROOT / ".cache" / f"chunks_{chunker}.json"
        if not chunk_path.exists():
            raise FileNotFoundError(f"Missing {chunk_path}; run `python src/index.py`")
        self.chunks = load_json(chunk_path)
        if not self.chunks:
            raise ValueError(f"No chunks in {chunk_path}")
        self.by_id = {chunk["id"]: chunk for chunk in self.chunks}
        collection_name = f"{chunker}_{'t' if add_title else 'p'}"
        vector_path = ROOT / ".cache" / f"vectors_{collection_name}.npz"
        if not vector_path.exists():
            raise FileNotFoundError(f"Missing {vector_path}; run `python src/index.py`")
        with np.load(vector_path) as stored:
            self.embeddings = stored["embeddings"]
        if len(self.embeddings) != len(self.chunks):
            raise ValueError(f"Vector/chunk count mismatch for {collection_name}")
        docs = [
            f"{chunk['title']} {chunk['text']}" if add_title else chunk["text"]
            for chunk in self.chunks
        ]
        self.bm25 = BM25Okapi([tokenize(doc) for doc in docs])

    def _vector(self, question: str, count: int) -> list[str]:
        query = (PREFIX if self.use_prefix else "") + question
        embedding = np.asarray(
            self.model.encode([query], normalize_embeddings=True)[0],
            dtype=np.float32,
        )
        if embedding.shape != (self.embeddings.shape[1],):
            raise ValueError(
                f"Query embedding dimension {embedding.shape} does not match index "
                f"dimension {self.embeddings.shape[1]}"
            )
        scores = self.embeddings @ embedding
        indices = np.argsort(scores)[::-1][:count]
        return [self.chunks[int(index)]["id"] for index in indices]

    def _bm25(self, question: str, count: int) -> list[str]:
        import numpy as np

        scores = self.bm25.get_scores(tokenize(question))
        indices = np.argsort(scores)[::-1][:count]
        return [self.chunks[int(index)]["id"] for index in indices]

    def retrieve(
        self, question: str, search: str = "vector", rerank: bool = False,
        k: int = 4, n: int = 20,
    ) -> tuple[list[dict], list[float] | None]:
        if search not in SEARCH_TYPES:
            raise ValueError(f"search must be one of {sorted(SEARCH_TYPES)}")
        if k <= 0 or n <= 0:
            raise ValueError("k and n must be positive")
        count = min(max(n, k), len(self.chunks))
        if search == "vector":
            ids = self._vector(question, count)
        elif search == "bm25":
            ids = self._bm25(question, count)
        else:
            ids = rrf([self._vector(question, count), self._bm25(question, count)])[:count]
        candidates = [self.by_id[chunk_id] for chunk_id in ids]
        if not rerank or not candidates:
            return candidates[:k], None
        scores = np.asarray(self.reranker.predict(
            [(question, chunk["text"]) for chunk in candidates]
        )).reshape(-1)
        order = np.argsort(-scores)
        return (
            [candidates[int(index)] for index in order[:k]],
            [float(scores[int(index)]) for index in order[:k]],
        )
