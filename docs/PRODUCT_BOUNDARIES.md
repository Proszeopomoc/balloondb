# Product boundaries

## Core

BalloonDB core contains:
- seed/bridge/route/index/WAL/recovery formats,
- BQL parser/planner/executor/query contracts,
- source memory and hydration contracts,
- deterministic tests and benchmarks.

## Not core

These are not core:
- BalloonOperator runtime,
- local AI/LM Studio/Ollama/OpenAI adapters,
- G5 autonomy/backlog/self-repair/overnight runners,
- workspaces, logs, compiled artifacts,
- large `.bpack` runtime memories.

## Rule

Operator and AI may call BalloonDB through API, but they do not define database truth. AI may create RAW/HYPOTHESIS/CANDIDATE records, not VERIFIED/PROMOTED without evidence.
