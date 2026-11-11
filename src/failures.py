import csv

from common import ROOT, load_json
from metrics import covered, score_question
from retrievers import Retriever


def main() -> None:
    config = load_json("config/best.json")
    questions = [
        question for question in load_json("data/testset_dev.json")
        if question["passages"]
    ]
    ret = Retriever(config["chunker"], add_title=config["add_title"])
    output = ROOT / "results" / "failures.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "id", "question", "expected", "rank_in_top20", "top1_file",
            "top1_text", "cause",
        ])
        for question in questions:
            top, _ = ret.retrieve(
                question["question"], config["search"], config["rerank"], k=20
            )
            if score_question(question, top, 4)["ok"]:
                continue
            rank = next((
                index + 1 for index, chunk in enumerate(top)
                if any(covered(chunk, passage) for passage in question["passages"])
            ), "not in top 20")
            first = top[0] if top else {"file": "", "text": ""}
            writer.writerow([
                question["id"], question["question"], question["expected_answer"],
                rank, first["file"], first["text"][:200].replace("\n", " "), "",
            ])
    print(f"Wrote failure review rows to {output}")


if __name__ == "__main__":
    main()
