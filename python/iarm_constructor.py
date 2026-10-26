#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

EVIDENCE = {"OBSERVED", "INFERRED", "UNRESOLVED"}
PROVENANCE = {"ORIGINAL", "TRANSFORMED", "HUMAN_CORRECTION", "SYSTEM_GENERATED", "SYNTHETIC"}
CODING = {"MATCH", "PARTIAL", "ABSENT", "CONTRADICTED", "UNRESOLVED"}
MANIFEST = {"RECORDED", "UNAVAILABLE", "NOT_APPLICABLE"}

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def require(rows, columns, name):
    if not rows:
        raise ValueError(f"{name} is empty")
    missing = set(columns) - set(rows[0])
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")

def load(folder):
    folder = Path(folder)
    artifacts = read_csv(folder / "artifacts.csv")
    observations = read_csv(folder / "observations.csv")
    coding = read_csv(folder / "recoverability_coding.csv")
    manifest = read_csv(folder / "run_manifest.csv")
    require(artifacts, ["artifact_id", "sequence", "parent_id", "content", "provenance_status"], "artifacts")
    require(observations, ["observation_id", "from_artifact", "to_artifact", "dimension", "status", "claim"], "observations")
    require(coding, ["construct_id", "status", "evidence_artifact_ids"], "coding")
    require(manifest, ["field", "value", "status"], "manifest")
    return artifacts, observations, coding, manifest

def validate(folder):
    artifacts, observations, coding, manifest = load(folder)
    ids = [row["artifact_id"] for row in artifacts]
    if len(ids) != len(set(ids)):
        raise ValueError("artifact IDs are not unique")
    sequence = [int(row["sequence"]) for row in artifacts]
    if sequence != sorted(sequence) or len(sequence) != len(set(sequence)):
        raise ValueError("artifact sequence must be unique and ascending")
    seen = set()
    for row in artifacts:
        if row["provenance_status"] not in PROVENANCE:
            raise ValueError(f"invalid provenance status: {row['provenance_status']}")
        for parent in filter(None, row["parent_id"].split(";")):
            if parent not in seen:
                raise ValueError(f"parent {parent} must precede {row['artifact_id']}")
        seen.add(row["artifact_id"])
    for row in observations:
        if row["status"] not in EVIDENCE:
            raise ValueError(f"invalid evidence status: {row['status']}")
        if row["from_artifact"] not in seen or row["to_artifact"] not in seen:
            raise ValueError(f"unknown artifact in {row['observation_id']}")
    for row in coding:
        if row["status"] not in CODING:
            raise ValueError(f"invalid coding status: {row['status']}")
        for artifact_id in filter(None, row["evidence_artifact_ids"].split(";")):
            if artifact_id not in seen:
                raise ValueError(f"unknown evidence artifact {artifact_id}")
    for row in manifest:
        if row["status"] not in MANIFEST:
            raise ValueError(f"invalid manifest status: {row['status']}")
    return artifacts, observations, coding, manifest

def summary(folder):
    artifacts, observations, coding, manifest = validate(folder)
    count = lambda rows, key, value: sum(row[key] == value for row in rows)
    total = len(coding)
    score = (count(coding, "status", "MATCH") + 0.5 * count(coding, "status", "PARTIAL")) / total
    return [
        ("artifact_count", str(len(artifacts))),
        ("observation_count", str(len(observations))),
        ("observed_count", str(count(observations, "status", "OBSERVED"))),
        ("inferred_count", str(count(observations, "status", "INFERRED"))),
        ("unresolved_count", str(count(observations, "status", "UNRESOLVED"))),
        ("method_construct_count", str(total)),
        ("match_count", str(count(coding, "status", "MATCH"))),
        ("partial_count", str(count(coding, "status", "PARTIAL"))),
        ("absent_count", str(count(coding, "status", "ABSENT"))),
        ("coding_unresolved_count", str(count(coding, "status", "UNRESOLVED"))),
        ("manifest_unavailable_count", str(sum(row["status"] == "UNAVAILABLE" for row in manifest))),
        ("descriptive_recoverability_score", f"{score:.3f}"),
    ]

def write_summary(rows, output):
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["metric", "value"])
        writer.writerows(rows)

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"validate", "summarize"}:
        raise SystemExit("usage: iarm_constructor.py validate FOLDER | summarize FOLDER OUTPUT")
    if sys.argv[1] == "validate":
        validate(sys.argv[2])
        print("VALIDATION_PASS")
    else:
        if len(sys.argv) != 4:
            raise SystemExit("summarize requires FOLDER OUTPUT")
        write_summary(summary(sys.argv[2]), sys.argv[3])
        print("SUMMARY_PASS")

if __name__ == "__main__":
    main()
