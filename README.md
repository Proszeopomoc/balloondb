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
