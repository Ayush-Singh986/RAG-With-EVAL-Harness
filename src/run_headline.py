import csv

from common import ROOT, load_json
from metrics import run_setup
from retrievers import Retriever


def main() -> None:
    config = load_json("config/best.json")
    questions = load_json("data/testset_main.json")
    setups = [
        ("Simple chunking", "fixed500", "vector", False),
        ("Semantic chunking", "semantic", "vector", False),
        ("Hybrid search", config["chunker"], "hybrid", False),
        ("Reranking", config["chunker"], "hybrid", True),
    ]
    output = ROOT / "results" / "headline.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "method", "chunker", "search", "rerank", "n", "hit", "full",
            "recall", "mrr", "ms_per_q",
        ])
        writer.writeheader()
        for label, chunker, search, rerank in setups:
            ret = Retriever(chunker, add_title=config["add_title"])
            aggregate, _ = run_setup(ret, questions, search, rerank)
            row = {
                "method": label, "chunker": chunker, "search": search,
                "rerank": rerank, **aggregate,
            }
            writer.writerow(row)
            print(row)
    print(f"Wrote headline comparisons to {output}")


if __name__ == "__main__":
    main()
