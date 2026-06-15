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
