# Results

Run `python run_experiment.py` to regenerate the ignored CSV, JSON, and PNG
artifacts from the deterministic synthetic panel. The outputs are deliberately
not committed as performance claims; CI verifies that they can be reproduced.

`public_market/` contains committed derived results from the official Kenneth
French monthly factor archives. It includes held-out metrics, row-level test
predictions, a rolling forecast diagnostic, and metadata with source URLs and
archive SHA-256 hashes. The raw ZIP archives remain ignored under `data/raw/`.
