# Data

- `DATA_VERSION.txt` records the upstream handbook Git commit used by `fetch_data.py`.
- `ATTRIBUTION.txt` records the source and licensing caution.
- `raw/` contains the sampled upstream Markdown files.
- `clean/` contains cleaned source text. Passage offsets and retrieval evaluation must use this text.
- `titles.json` maps cleaned filenames to document titles.
- `testset_main_src.json` and `testset_dev_src.json` are human-reviewed source question sets to create. Exact answer passages belong here before `build_testset.py` calculates offsets.
- `testset_main.json` and `testset_dev.json` are generated offset-bearing sets. Do not edit their offsets by hand.

The handbook corpus is present in `clean/`; the reviewed question sets have not been fabricated or supplied.
