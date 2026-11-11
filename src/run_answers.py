import argparse
import csv

from common import ROOT, load_json
from generate import evaluate
from retrievers import Retriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", action="store_true", help="Answer without retrieval")
    parser.add_argument("--limit", type=int, help="Optional question limit for a smoke run")
    args = parser.parse_args()
    questions = load_json("data/testset_main.json")
    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be positive")
        questions = questions[:args.limit]
    ret = None
    if not args.control:
        from common import load_json as load_config
        from sentence_transformers import CrossEncoder, SentenceTransformer
        from common import MODEL_NAME, RERANK_NAME

        config = load_config("config/best.json")
        ret = Retriever(
            config["chunker"], add_title=config["add_title"],
            model=SentenceTransformer(MODEL_NAME), reranker=CrossEncoder(RERANK_NAME),
        )
    output = ROOT / "results" / (
        "answers_control.csv" if args.control else "answers_main.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "id", "question", "expected_answer", "answer", "correct", "faithful",
            "latency_ms", "control",
        ])
        writer.writeheader()
        for question in questions:
            chunks = []
            if ret is not None:
                chunks, _ = ret.retrieve(
                    question["question"], config["search"], config["rerank"]
                )
            result = evaluate(question, chunks, control=args.control)
            writer.writerow({
                "id": question["id"], "question": question["question"],
                "expected_answer": question["expected_answer"], **result,
                "control": args.control,
            })
            handle.flush()
            print(f"#{question['id']}: correct={result['correct']} {result['latency_ms']}ms")
    print(f"Saved answers to {output}")


if __name__ == "__main__":
    main()
