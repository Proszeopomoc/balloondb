# BalloonDB API Spec

## Core concepts

- Seed: atomic memory concept or fact.
- Bridge: typed relation between seeds.
- Route: traversable path through memory graph.
- Evidence: deterministic support for a record.
- Trust state: verification state of a record.
- BQL query: query executed against BalloonDB memory.

## Minimum API surface

### Open database

Input:

- database root path

Output:

- database handle or error envelope

### Write seed

Input:

- seed payload
- source
- trust state
- evidence reference

Output:

- seed id
- write status

### Write bridge

Input:

- source seed id
- target seed id
- relation type
- trust state
- evidence reference

Output:

- bridge id
- write status

### Query BQL

Input:

- BQL query
- max results
- optional memory root

Output:

- ok envelope or error envelope

Every query error must return a stable error code, not an uncontrolled exception.
