# BQL spec V0

BQL is the database query language for BalloonDB.

Required v0 scope:
- parse query,
- plan local lookup,
- expand balloon by radius/direction/type filters,
- filter/rank results,
- return stable ok/error envelope,
- produce explain/query history traces,
- never execute arbitrary code.

BQL may return `HYDRATION_REQUIRED` for virtual/external nodes. That is not an error; it is a controlled continuation request.
