# Tests

- `test_pipeline.py` checks pure chunking, ranking, passage-scoring, and offset-building behavior.
- `test_testset.py` validates the reviewed main/dev dataset shape, exact passage offsets, and question separation when those generated sets exist. It is skipped until both sets are prepared.

Run all tests with `python -m pytest -q`.
