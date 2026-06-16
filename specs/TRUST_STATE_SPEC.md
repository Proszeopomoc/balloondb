# BalloonDB Trust State Spec

## States

### RAW

Unverified incoming data.

### HYPOTHESIS

Possible rule or relation. Can guide search, but cannot be treated as truth.

### CANDIDATE

Hypothesis with partial support. Still not authoritative.

### VERIFIED

Record supported by deterministic checks or reproducible evidence.

### PROMOTED

Verified record accepted into stable operational memory.

### QUARANTINED

Record blocked from active use due to contradiction, corruption, unsafe source, or failed validation.

### FROZEN

Historical evidence retained for audit. Not active runtime logic.

## Promotion rule

AI output alone cannot promote a record to VERIFIED or PROMOTED.
