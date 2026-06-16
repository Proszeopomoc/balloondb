# Benchmark plan

No superiority claims without benchmarks.

Initial benchmarks:
- Python reference append/read speed for `.bseed/.bbridge`.
- WAL append and recovery speed.
- `.bindex` lookup latency for 1k / 10k / 100k records.
- BQL local expand latency by radius.
- Source-memory hydration: cold vs cached lookup.

Baselines may include SQLite, Neo4j, Qdrant, JSONL and flat file lookup, but external DBs remain adapters, not BalloonDB core.
