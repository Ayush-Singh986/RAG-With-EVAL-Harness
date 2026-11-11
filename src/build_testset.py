import argparse
import sys

from common import ROOT, load_json, read, write_json

VALID_TYPES = {"direct", "paraphrased", "multi_document", "no_answer"}


def build(source: str, output: str) -> None:
    questions = load_json(source)
    if not isinstance(questions, list):
        raise ValueError(f"{source} must contain a JSON list")
    errors: list[str] = []
    seen_ids: set[str] = set()
    for question in questions:
        qid = str(question.get("id", ""))
        if not qid or qid in seen_ids:
            errors.append(f"missing or duplicate id {qid!r}")
        seen_ids.add(qid)
        if question.get("type") not in VALID_TYPES:
            errors.append(f"question {qid}: invalid type {question.get('type')!r}")
        passages = question.get("passages")
        if not isinstance(passages, list):
            errors.append(f"question {qid}: passages must be a list")
            continue
        if question.get("type") == "no_answer" and passages:
            errors.append(f"question {qid}: no_answer questions cannot have passages")
        for passage in passages:
            try:
                text = read(passage["file"])
            except (KeyError, OSError, ValueError) as exc:
                errors.append(f"question {qid}: invalid passage file: {exc}")
                continue
            excerpt = passage.get("text", "")
            start = text.find(excerpt)
            if not excerpt or start < 0:
                errors.append(f"question {qid}: exact passage not found in {passage['file']}")
                continue
            if text.find(excerpt, start + 1) >= 0:
                print(f"WARNING: passage appears more than once for question {qid}")
            passage["start"], passage["end"] = start, start + len(excerpt)
    if errors:
        raise ValueError("Invalid test set:\n" + "\n".join(errors))
    write_json(output, questions)
    print(f"Wrote {len(questions)} questions to {ROOT / output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-src", default="data/testset_main_src.json")
    parser.add_argument("--dev-src", default="data/testset_dev_src.json")
    args = parser.parse_args()
    try:
        build(args.main_src, "data/testset_main.json")
        build(args.dev_src, "data/testset_dev.json")
    except (OSError, ValueError, KeyError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
