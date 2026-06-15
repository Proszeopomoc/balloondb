# BalloonDB Binary Transaction V00M1

V00M1 fixes the transaction selftest and the product gate behavior after V00M.

## Guarantees tested

- versioned snapshot directories
- staged snapshot not active until CURRENT is atomically replaced
- CURRENT pointer activation
- fallback to the latest previous complete snapshot
- CRC/SHA corruption detection
- product gate fails if a subrunner fails

Stable tag target: `v0.0.10-binary-transaction-gate-fixed`.
