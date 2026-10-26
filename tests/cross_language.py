#!/usr/bin/env python3
"""Cross-language checks for the synthetic IARM constructor."""

import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_transformation"
PYTHON = [sys.executable, str(ROOT / "python" / "iarm_constructor.py")]
RSCRIPT = ["Rscript", str(ROOT / "r" / "iarm_constructor.R")]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def validate(folder):
    py = run(PYTHON + ["validate", str(folder)])
    r = run(RSCRIPT + ["validate", str(folder)])
    return py.returncode == 0 and r.returncode == 0, py, r


def summarize(folder):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        py_out = tmp / "python.csv"
        r_out = tmp / "r.csv"
        py = run(PYTHON + ["summarize", str(folder), str(py_out)])
        r = run(RSCRIPT + ["summarize", str(folder), str(r_out)])
        if py.returncode != 0 or r.returncode != 0:
            raise SystemExit(f"summarize failed\n{py.stderr}\n{r.stderr}")
        with py_out.open(encoding="utf-8") as handle:
            py_rows = {row["metric"]: row["value"] for row in csv.DictReader(handle)}
        with r_out.open(encoding="utf-8") as handle:
            r_rows = {row["metric"]: row["value"] for row in csv.DictReader(handle)}
        return py_rows, r_rows


def copy_example(tmp):
    dest = Path(tmp) / "corpus"
    shutil.copytree(EXAMPLE, dest)
    return dest


def replace(path, old, new):
    file = Path(path)
    file.write_text(file.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")


def expect_reject(name, mutate):
    with tempfile.TemporaryDirectory() as tmp:
        folder = copy_example(tmp)
        mutate(folder)
        ok, py, r = validate(folder)
        if ok:
            raise SystemExit(f"FAIL {name}: both languages accepted an invalid corpus")
        if py.returncode == 0:
            raise SystemExit(f"FAIL {name}: Python accepted an invalid corpus")
        if r.returncode == 0:
            raise SystemExit(f"FAIL {name}: R accepted an invalid corpus")
    print(f"REJECT_PASS {name}")


def main():
    demo = run(["sh", str(ROOT / "scripts" / "run_demo.sh")])
    if demo.returncode != 0 or "CROSS_LANGUAGE_PASS" not in demo.stdout:
        raise SystemExit(f"FAIL demo\n{demo.stdout}\n{demo.stderr}")
    print("DEMO_PASS")

    py_rows, r_rows = summarize(EXAMPLE)
    if py_rows != r_rows:
        raise SystemExit(f"FAIL example summary mismatch\n{py_rows}\n{r_rows}")
    if py_rows["descriptive_recoverability_score"] != "0.500":
        raise SystemExit(f"FAIL unexpected example score {py_rows['descriptive_recoverability_score']}")
    print("SUMMARY_MATCH")

    expect_reject(
        "sequence",
        lambda folder: replace(folder / "artifacts.csv", "A002,2,", "A002,9,"),
    )
    expect_reject(
        "parent_order",
        lambda folder: replace(
            folder / "artifacts.csv",
            "A003,3,correction,researcher,researcher,A002,",
            "A003,3,correction,researcher,researcher,A006,",
        ),
    )
    expect_reject(
        "evidence_status",
        lambda folder: replace(folder / "observations.csv", ",OBSERVED,", ",MAYBE,"),
    )
    expect_reject(
        "provenance",
        lambda folder: replace(folder / "artifacts.csv", ",SYSTEM_GENERATED", ",GUESS"),
    )
    expect_reject(
        "coding_status",
        lambda folder: replace(folder / "recoverability_coding.csv", ",MATCH,", ",MAYBE,"),
    )
    expect_reject(
        "manifest_status",
        lambda folder: replace(folder / "run_manifest.csv", ",RECORDED", ",MAYBE"),
    )
    expect_reject(
        "evidence_artifact",
        lambda folder: replace(folder / "recoverability_coding.csv", ",A006,", ",A999,"),
    )
    expect_reject(
        "empty_coding",
        lambda folder: (folder / "recoverability_coding.csv").write_text(
            "construct_id,status,evidence_artifact_ids,coder_note\n",
            encoding="utf-8",
        ),
    )

    with tempfile.TemporaryDirectory() as tmp:
        folder = copy_example(tmp)
        replace(
            folder / "recoverability_coding.csv",
            "reconstruction_before_interpretation,MATCH,",
            "reconstruction_before_interpretation,CONTRADICTED,",
        )
        py_rows, r_rows = summarize(folder)
        if py_rows != r_rows:
            raise SystemExit(f"FAIL contradicted mismatch\n{py_rows}\n{r_rows}")
        if py_rows["descriptive_recoverability_score"] != "0.333":
            raise SystemExit(f"FAIL contradicted score {py_rows['descriptive_recoverability_score']}")
        if py_rows["match_count"] != "1":
            raise SystemExit(f"FAIL contradicted match count {py_rows['match_count']}")
    print("CONTRADICTED_PASS")
    print("CROSS_LANGUAGE_TESTS_PASS")


if __name__ == "__main__":
    main()
