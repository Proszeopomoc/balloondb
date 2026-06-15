# BalloonDB repo cleanup V00C status

This cleanup stage freezes the broken V03H4A path and installs a target-state BQL compatibility gate V03H4B.

## Decisions

- V03H4A is frozen because it contained a top-level `HELPER = r` NameError.
- V03H4B is the active BQL compatibility target.
- BQL error envelopes now expose stable `ok_envelope`, `error_envelope`, `write_json`, `write_jsonl`, and `write_html_report` functions.
- G1/G2 BQL selftests are made compatible with the current executor output (`balloon_expand`) instead of the older removed `seed_lookup` field.
- H4B uses local synthetic memory only; it does not read live operator memory, call APIs, or launch runtime agents.

## Remaining cleanup after V00C

- Full script portability audit: old Windows scripts may still contain legacy `C:\BalloonOperator` defaults.
- Move generated runtime outputs under ignore/example policy before public repo push.
- Add Rust hot-path only after format/API contracts are stable.
