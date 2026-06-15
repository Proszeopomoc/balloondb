# BalloonDB Agent Contract

This repository is the standalone BalloonDB product repository.

Rules:
- Do not write generated audit/build/runtime artifacts into Git.
- Every product change must pass the product gate.
- Product gate must fail-closed on missing files, runner failures, compile failures, tracked generated files, or hardcoded active roots.
- Python and Rust implementations must preserve the same public binary format unless a migration gate explicitly approves a new format.
- BRS1 is a lab/legacy Rust format and is not the default BalloonDB storage format.
- V00J .bseed/.bbridge compatibility is the current cross-language boundary.
- Fresh clone verification is required before treating a tag as stable.
