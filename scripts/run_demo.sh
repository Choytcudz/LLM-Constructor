#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
example="$root/examples/synthetic_transformation"
results="$root/results"
mkdir -p "$results"

python3 "$root/python/iarm_constructor.py" validate "$example"
Rscript "$root/r/iarm_constructor.R" validate "$example"
python3 "$root/python/iarm_constructor.py" summarize "$example" "$results/python.csv"
Rscript "$root/r/iarm_constructor.R" summarize "$example" "$results/r.csv"

python3 - "$results/python.csv" "$results/r.csv" <<'PY'
import csv
import sys

def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["metric"]: row["value"] for row in csv.DictReader(handle)}

if load(sys.argv[1]) != load(sys.argv[2]):
    raise SystemExit("CROSS_LANGUAGE_MISMATCH")
print("CROSS_LANGUAGE_PASS")
PY
