import json

import numpy as np
import pytest

from build_testset import build
from chunkers import by_heading, fixed, sentence_spans
from common import ROOT
from metrics import covered, score_question
from retrievers import Retriever, rrf


def test_fixed_chunks_cover_text_and_respect_overlap():
    text = "abcdefghij"
    spans = fixed(text, size=4, overlap=1)
    assert spans == [(0, 4), (3, 7), (6, 10)]
    assert "".join(text[start:end] for start, end in spans)


@pytest.mark.parametrize("size,overlap", [(0, 0), (3, 3), (3, -1)])
def test_fixed_rejects_invalid_sizes(size, overlap):
    with pytest.raises(ValueError):
        fixed("text", size=size, overlap=overlap)


def test_heading_chunk_positions_are_valid():
    text = "# A\n" + "alpha " * 80 + "\n## B\n" + "beta " * 80
    spans = by_heading(text, max_len=200, min_len=20)
    assert spans
    assert all(0 <= start < end <= len(text) for start, end in spans)


def test_sentence_spans_cover_nonempty_segments():
    text = "First sentence. Second sentence!\n\nThird sentence?"
    spans = sentence_spans(text)
    assert [text[start:end] for start, end in spans] == [
        "First sentence.", "Second sentence!", "Third sentence?"
    ]


def test_rrf_merges_by_rank_and_deduplicates():
    assert rrf([["a", "b"], ["b", "c"]]) == ["b", "a", "c"]


def test_vector_search_uses_cosine_similarity_order():
    class Model:
        def encode(self, texts, normalize_embeddings):
            assert normalize_embeddings
            return np.array([[1.0, 0.0]], dtype=np.float32)

    ret = Retriever.__new__(Retriever)
    ret.model = Model()
    ret.use_prefix = False
    ret.embeddings = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    ret.chunks = [{"id": "lower"}, {"id": "best"}]
    assert ret._vector("query", 1) == ["best"]


def test_passage_coverage_requires_same_file_and_half_overlap():
    passage = {"file": "a.md", "start": 10, "end": 20}
    assert covered({"file": "a.md", "start": 5, "end": 15}, passage)
    assert not covered({"file": "a.md", "start": 5, "end": 14}, passage)
    assert not covered({"file": "b.md", "start": 10, "end": 20}, passage)


def test_multidocument_scoring_requires_all_passages():
    question = {
        "id": 1, "passages": [
            {"file": "a.md", "start": 0, "end": 10},
            {"file": "b.md", "start": 0, "end": 10},
        ],
    }
    chunks = [{"file": "a.md", "start": 0, "end": 10}]
    assert score_question(question, chunks, 4) == {
        "id": 1, "hit": True, "ok": False, "recall": 0.5, "mrr": 1.0,
    }


def test_build_testset_computes_exact_positions(tmp_path):
    clean_dir = ROOT / "data" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    doc = clean_dir / "test-fixture.md"
    original = doc.read_text(encoding="utf-8") if doc.exists() else None
    doc.write_text("Header\nExact answer sentence.\n", encoding="utf-8")
    source = tmp_path / "source.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps([{
        "id": 1, "question": "What is the answer?", "type": "direct",
        "expected_answer": "Exact answer.", "passages": [{
            "file": "test-fixture.md", "text": "Exact answer sentence.",
        }],
    }]), encoding="utf-8")
    try:
        build(str(source), str(output))
        result = json.loads(output.read_text(encoding="utf-8"))
        passage = result[0]["passages"][0]
        assert doc.read_text(encoding="utf-8")[passage["start"]:passage["end"]] == passage["text"]
    finally:
        doc.unlink(missing_ok=True)
        if original is not None:
            doc.write_text(original, encoding="utf-8")
