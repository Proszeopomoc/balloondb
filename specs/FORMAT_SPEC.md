# BalloonDB Format Spec

## Runtime formats

- .bseed   â€” binary seed records
- .bbridge â€” binary bridge records
- .bwal    â€” write-ahead log
- .bindex  â€” index file
- .broute  â€” route file
- .bpack   â€” pack/archive format

## Human-readable formats

- .json
- .jsonl
- .md
- .html
- .csv

Human-readable files are allowed for audit, debugging, reports, examples, and migration. They are not the target hot-path runtime format.

## Generated outputs

Generated test outputs must not be committed to Git unless explicitly promoted as fixtures.
