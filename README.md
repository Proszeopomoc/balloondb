# BalloonDB

BalloonDB is an agent-native memory database for graph memory, evidence, routes, query traces, and verifiable promotion states.

Current status:

- Python reference implementation
- Storage / WAL / crash recovery selftests
- BQL compatibility gate
- Root-portable fresh clone verified
- Generated outputs excluded from Git
- Broken V03H4A frozen
- Active BQL target: V03H4B

## Stable tags

- v0.0.1-root-portable
- v0.0.2-repo-hygiene
- v0.0.3-product-gate
- v0.0.4-agpl-license

## Product boundary

BalloonDB is the database layer.

It is not:

- the full BalloonOperator runtime
- an AI model
- an autonomous patching agent
- a truth source controlled by an LLM

AI systems may write RAW, HYPOTHESIS, and CANDIDATE records. Promotion to VERIFIED or PROMOTED requires deterministic evidence.

## Product gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_PRODUCT_GATE_V00G.ps1"
```

Expected:

```text
PASS_BALLOONDB_PRODUCT_GATE_V00G
```

## License

BalloonDB is licensed under the GNU Affero General Public License version 3 only.

SPDX-License-Identifier: AGPL-3.0-only

Commercial use is allowed under AGPL-3.0 terms. If a company or project needs different terms, a separate commercial license may be negotiated with the copyright holder.

## Security and warranty

BalloonDB is experimental software provided as-is, without warranty. Use it at your own risk and do not use it for sensitive or production data without independent validation.


## V00J binary database core

BalloonDB now includes a first binary storage core for .bseed, .bbridge, .bwal, and .bdbm manifest files. Run scripts/windows/RUN_BINARY_FORMAT_SELFTEST_V00J.ps1 to verify write/read/WAL/replay/corrupt-detection behavior.


## V00K binary index and query

BalloonDB now includes .bindex support over V00J .bseed and .bbridge files, with lookup by record id, type, trust state, relation, and a minimal binary query subset. Run scripts/windows/RUN_BINARY_INDEX_QUERY_SELFTEST_V00K.ps1 to verify indexing and query behavior.


## V00L binary compaction and snapshot

BalloonDB now includes WAL compaction into binary snapshots, snapshot manifest generation, complete-snapshot recovery, and corrupt snapshot detection. Run `scripts/windows/RUN_BINARY_COMPACTION_SNAPSHOT_SELFTEST_V00L.ps1` to verify compaction and recovery behavior.

