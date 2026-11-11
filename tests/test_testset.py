from collections import Counter

import pytest

from common import ROOT, load_json, read

MAIN = ROOT / "data" / "testset_main.json"
DEV = ROOT / "data" / "testset_dev.json"
TESTSETS_READY = MAIN.exists() and DEV.exists()
pytestmark = pytest.mark.skipif(
    not TESTSETS_READY, reason="Build the reviewed main and dev test sets first"
)


def test_passage_offsets_match_cleaned_files():
    for path in (MAIN, DEV):
        for question in load_json(path):
            for passage in question["passages"]:
                assert read(passage["file"])[passage["start"]:passage["end"]] == passage["text"], question["id"]


def test_main_set_has_expected_shape():
    questions = load_json(MAIN)
    types = Counter(question["type"] for question in questions)
    assert len(questions) == 50
    assert types["direct"] == 20
    assert types["paraphrased"] == 12
    assert types["multi_document"] == 8
    assert types["no_answer"] == 10


def test_dev_set_is_large_enough_and_has_no_answer_questions():
    questions = load_json(DEV)
    assert len(questions) >= 100
    assert Counter(question["type"] for question in questions)["no_answer"] >= 15


def test_main_and_dev_questions_do_not_overlap():
    main_questions = {question["question"] for question in load_json(MAIN)}
    dev_questions = {question["question"] for question in load_json(DEV)}
    assert not main_questions & dev_questions
