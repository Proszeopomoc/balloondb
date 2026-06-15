# BalloonDB Product Architecture

## Layers

1. Storage layer
   - seed records
   - bridge records
   - WAL
   - recovery
   - index files

2. Query layer
   - BQL parser
   - BQL executor
   - query contract runner
   - error envelope contract

3. Trust layer
   - RAW
   - HYPOTHESIS
   - CANDIDATE
   - VERIFIED
   - PROMOTED
   - QUARANTINED
   - FROZEN

4. Client layer
   - CLI
   - daemon/client interface
   - future bindings

5. External agent layer
   - BalloonOperator
   - AI adapters
   - local/API model planners

Rule: BalloonDB stores memory and evidence. It does not delegate truth to an AI model.
