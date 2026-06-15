# Format spec V0

Runtime target formats:

- `.bseed` â€” facts, symbols, tasks, errors, rules, source refs.
- `.bbridge` â€” typed relations between seeds/records.
- `.broute` â€” proven traversals/repair/decision paths.
- `.bindex` â€” fast hash/token/source lookup.
- `.bpromote` â€” promoted high-confidence local rules.
- `.bwal` â€” append-only recovery/audit log.

Reference implementation starts in Python. Rust hot-path follows after the format contract and regression gates are stable.
