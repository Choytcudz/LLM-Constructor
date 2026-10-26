evidence <- c("OBSERVED", "INFERRED", "UNRESOLVED")
provenance <- c("ORIGINAL", "TRANSFORMED", "HUMAN_CORRECTION", "SYSTEM_GENERATED", "SYNTHETIC")
coding_status <- c("MATCH", "PARTIAL", "ABSENT", "CONTRADICTED", "UNRESOLVED")
manifest_status <- c("RECORDED", "UNAVAILABLE", "NOT_APPLICABLE")

read_table <- function(folder, name) {
  read.csv(file.path(folder, name), stringsAsFactors = FALSE, check.names = FALSE)
}

require_table <- function(dat, columns, name) {
  if (nrow(dat) == 0) stop(paste(name, "is empty"))
  missing <- setdiff(columns, names(dat))
  if (length(missing)) stop(paste(name, "missing columns:", paste(missing, collapse = ", ")))
}

validate_iarm <- function(folder) {
  artifacts <- read_table(folder, "artifacts.csv")
  observations <- read_table(folder, "observations.csv")
  coding <- read_table(folder, "recoverability_coding.csv")
  manifest <- read_table(folder, "run_manifest.csv")
  require_table(artifacts, c("artifact_id", "sequence", "parent_id", "content", "provenance_status"), "artifacts")
  require_table(observations, c("observation_id", "from_artifact", "to_artifact", "dimension", "status", "claim"), "observations")
  require_table(coding, c("construct_id", "status", "evidence_artifact_ids"), "coding")
  require_table(manifest, c("field", "value", "status"), "manifest")
  if (anyDuplicated(artifacts$artifact_id)) stop("artifact IDs are not unique")
  seqs <- as.integer(artifacts$sequence)
  if (is.unsorted(seqs) || anyDuplicated(seqs)) stop("artifact sequence must be unique and ascending")
  if (any(!artifacts$provenance_status %in% provenance)) stop("invalid provenance status")
  seen <- character()
  for (i in seq_len(nrow(artifacts))) {
    parents <- Filter(nzchar, strsplit(artifacts$parent_id[i], ";", fixed = TRUE)[[1]])
    if (length(setdiff(parents, seen))) stop("parent must precede child")
    seen <- c(seen, artifacts$artifact_id[i])
  }
  if (any(!observations$status %in% evidence)) stop("invalid evidence status")
  if (any(!observations$from_artifact %in% seen) || any(!observations$to_artifact %in% seen)) stop("unknown artifact")
  if (any(!coding$status %in% coding_status)) stop("invalid coding status")
  for (i in seq_len(nrow(coding))) {
    ids <- Filter(nzchar, strsplit(coding$evidence_artifact_ids[i], ";", fixed = TRUE)[[1]])
    if (length(setdiff(ids, seen))) stop("unknown evidence artifact")
  }
  if (any(!manifest$status %in% manifest_status)) stop("invalid manifest status")
  list(a = artifacts, o = observations, c = coding, m = manifest)
}

summarize_iarm <- function(folder) {
  x <- validate_iarm(folder)
  nstatus <- function(dat, value) sum(dat$status == value)
  score <- (nstatus(x$c, "MATCH") + 0.5 * nstatus(x$c, "PARTIAL")) / nrow(x$c)
  data.frame(metric = c("artifact_count", "observation_count", "observed_count", "inferred_count",
    "unresolved_count", "method_construct_count", "match_count", "partial_count", "absent_count",
    "coding_unresolved_count", "manifest_unavailable_count", "descriptive_recoverability_score"),
    value = c(nrow(x$a), nrow(x$o), nstatus(x$o, "OBSERVED"), nstatus(x$o, "INFERRED"),
      nstatus(x$o, "UNRESOLVED"), nrow(x$c), nstatus(x$c, "MATCH"), nstatus(x$c, "PARTIAL"),
      nstatus(x$c, "ABSENT"), nstatus(x$c, "UNRESOLVED"), sum(x$m$status == "UNAVAILABLE"),
      sprintf("%.3f", score)), stringsAsFactors = FALSE)
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2 || !args[1] %in% c("validate", "summarize")) stop("usage: validate FOLDER | summarize FOLDER OUTPUT")
if (args[1] == "validate") {
  validate_iarm(args[2]); cat("VALIDATION_PASS\n")
} else {
  if (length(args) != 3) stop("summarize requires FOLDER OUTPUT")
  dir.create(dirname(args[3]), recursive = TRUE, showWarnings = FALSE)
  write.csv(summarize_iarm(args[2]), args[3], row.names = FALSE, quote = FALSE)
  cat("SUMMARY_PASS\n")
}
