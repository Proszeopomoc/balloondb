# BalloonDB

Agent-native binary memory database.

BalloonDB is a database engine for AI agents: seeds, balloons, bridges, evidence, routes, binary storage, WAL/recovery, BQL, source memory and safe agent/model APIs.

This repository is the clean BalloonDB core. It intentionally excludes BalloonOperator runtime, G5 autonomy, large local `.bpack` packs, logs, workspaces and API materializations.

## Product boundary

- BalloonDB = database + engine.
- BalloonOperator = client, later.
- AI adapters = clients, later.
- External databases = adapters/providers, not core.
- JSON/HTML = audit and debug.
- Binary `.bseed/.bbridge/.broute/.bindex/.bpromote/.bwal` = runtime target.

## Current staged contents

- `python_ref/balloondb_core/` â€” Python reference implementation and selftests.
- `scripts/windows/` â€” reviewed Windows wrappers for core tests.
- `examples/` â€” tiny binary/index/WAL examples only.
- `specs/` â€” product-level format/query/source-memory contracts.
- `_frozen/` â€” frozen autonomy drift note only, not runnable autonomy.
