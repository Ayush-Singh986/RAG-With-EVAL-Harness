import csv

import numpy as np

from common import ROOT, load_json
from retrievers import Retriever


def main() -> None:
    config = load_json("config/best.json")
    if not config["rerank"]:
        raise ValueError("Threshold calibration requires reranking to be enabled")
    questions = load_json("data/testset_dev.json")
    answerable = [question for question in questions if question["passages"]]
    no_answer = [question for question in questions if not question["passages"]]
    if not answerable or not no_answer:
        raise ValueError("The dev set must contain answerable and no-answer questions")
    ret = Retriever(config["chunker"], add_title=config["add_title"])

    def top_scores(group: list[dict]) -> list[float]:
        scores = []
        for question in group:
            _, rerank_scores = ret.retrieve(
                question["question"], config["search"], True, k=1, n=20
            )
            if not rerank_scores:
                raise RuntimeError(f"No reranker score returned for question {question['id']}")
            scores.append(rerank_scores[0])
        return scores

    answerable_scores = top_scores(answerable)
    no_answer_scores = top_scores(no_answer)
    output = ROOT / "results" / "thresholds.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["threshold", "no_answer_refused", "answerable_refused"])
        for threshold in np.arange(-10, 10.5, 0.5):
            writer.writerow([
                round(float(threshold), 1),
                round(float(np.mean([score < threshold for score in no_answer_scores])), 3),
                round(float(np.mean([score < threshold for score in answerable_scores])), 3),
            ])
    print(f"Wrote threshold trade-offs to {output}")


if __name__ == "__main__":
    main()
