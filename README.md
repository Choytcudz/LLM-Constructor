# LLM Constructor: IARM prototype

An offline, cross-language prototype of Joseph C. Hoyt's Interaction Artifact
Reconstruction Methodology (IARM). It reconstructs an ordered interaction
corpus before interpretation and keeps `OBSERVED`, `INFERRED`, and `UNRESOLVED`
claims separate.

The included transformation experiment is synthetic. It models the author's
method-recoverability design: a constructor produces artifacts, corrections
remain in the corpus, and a blind evaluator attempts to recover the visible
method without receiving its formal definition. Recoverability is not validity.

## Run

```zsh
./scripts/run_demo.sh
python3 tests/cross_language.py
```

The descriptive score is `(MATCH + 0.5 * PARTIAL) / coding rows`. `ABSENT`,
`CONTRADICTED`, and `UNRESOLVED` stay in the denominator and add nothing to
the numerator. An empty coding table is a validation failure.

Or run either implementation directly:

```zsh
python3 python/iarm_constructor.py summarize examples/synthetic_transformation results/python.csv
Rscript r/iarm_constructor.R summarize examples/synthetic_transformation results/r.csv
```

Both implementations use only their standard libraries. They validate artifact
sequence, parent links, evidence statuses, provenance status, experimental
condition recording, and human-coded recoverability judgments.

## Experimental controls

Record model, version, product, visible prompt, available system instructions,
memory, tools, retrieval, context, temperature or seed, and time. Unknown fields
remain `UNAVAILABLE`; they are never silently treated as controlled.

The public example contains no real research subjects, private communications,
or model transcripts. LLM output is an artifact and lead, not evidence of hidden
cognition, intent, or a legal conclusion.

Copyright © 2026 Joseph C. Hoyt. All rights reserved. The initial repository
commit contained only a CC0 license. This later prototype is not released under
CC0. OpenAI Codex assisted implementation and is not represented as co-owner.
