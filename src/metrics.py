import time


def covered(chunk: dict, passage: dict) -> bool:
    if chunk["file"] != passage["file"]:
        return False
    overlap = min(chunk["end"], passage["end"]) - max(chunk["start"], passage["start"])
    return overlap >= 0.5 * (passage["end"] - passage["start"])


def score_question(question: dict, chunks: list[dict], k: int = 4) -> dict:
    if k <= 0:
        raise ValueError("k must be positive")
    passages = question["passages"]
    if not passages:
        raise ValueError("Passage-retrieval metrics require an answerable question")
    top = chunks[:k]
    got = [any(covered(chunk, passage) for chunk in top) for passage in passages]
    ranks = [
        rank for rank, chunk in enumerate(top)
        if any(covered(chunk, passage) for passage in passages)
    ]
    return {
        "id": question["id"], "hit": any(got), "ok": all(got),
        "recall": sum(got) / len(got),
        "mrr": 1 / (ranks[0] + 1) if ranks else 0.0,
    }


def run_setup(ret, questions: list[dict], search: str, rerank: bool, k: int = 4):
    start_time = time.perf_counter()
    rows = []
    answerable = [question for question in questions if question["passages"]]
    for question in answerable:
        chunks, _ = ret.retrieve(question["question"], search, rerank, k=max(k, 20))
        rows.append(score_question(question, chunks, k))
    if not rows:
        raise ValueError("Cannot score a test set with no answerable questions")
    count = len(rows)
    aggregate = {
        "n": count,
        "hit": sum(row["hit"] for row in rows),
        "full": sum(row["ok"] for row in rows),
        "recall": round(sum(row["recall"] for row in rows) / count, 3),
        "mrr": round(sum(row["mrr"] for row in rows) / count, 3),
        "ms_per_q": round(1000 * (time.perf_counter() - start_time) / count),
    }
    return aggregate, rows
