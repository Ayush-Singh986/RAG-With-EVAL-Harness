import argparse
import sys

from common import load_json, write_json
from metrics import run_setup
from retrievers import Retriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    config = load_json("config/best.json")
    ret = Retriever(config["chunker"], add_title=config["add_title"])
    questions = load_json("data/testset_main.json")
    aggregate, rows = run_setup(ret, questions, config["search"], config["rerank"])
    now = {str(row["id"]): row["ok"] for row in rows}
    print(aggregate)
    if args.update:
        write_json(args.baseline, now)
        return
    baseline = load_json(args.baseline)
    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("Baseline must be a non-empty JSON object of question IDs to booleans")
    text = {str(question["id"]): question["question"] for question in questions}
    broken = [qid for qid, passed in baseline.items() if passed and not now.get(qid, False)]
    if broken:
        print("REGRESSION. These previously passing questions now fail:")
        for qid in broken:
            print(f"  #{qid}: {text.get(qid, '[question missing from test set]')}")
        sys.exit(1)
    print("OK, no regressions")


if __name__ == "__main__":
    main()
