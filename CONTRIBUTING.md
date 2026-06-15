# Contributing

BalloonDB is licensed under AGPL-3.0-only.

By submitting a contribution, you agree that your contribution is provided under the same AGPL-3.0-only license unless a separate written agreement says otherwise.

## Rules

- Do not commit secrets, API keys, credentials, private data, or generated runtime outputs.
- Do not commit large generated audit/data/report files.
- Run the product gate before submitting changes.
- Keep BalloonDB separate from BalloonOperator-specific runtime state.
- Keep AI/model-generated suggestions in RAW, HYPOTHESIS, or CANDIDATE state unless deterministic evidence promotes them.

## Product gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_PRODUCT_GATE_V00G.ps1"
```
