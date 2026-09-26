# Final submission report

## Executive summary

BoundaryCheck is a local, deterministic CLI that reviews declared AI deployment settings before a customer pilot. It turns a small JSON profile into prioritized findings with source paths, plain-language impact, and next steps. The tool is aimed at the moment between a successful prototype and a production-readiness conversation, when security and operating assumptions need to become explicit.

## Delivery completed

- Reviewed a sample of high-compensation FDE and forward-deployed security job postings and recorded compensation plus repeated skills in [`research.md`](research.md).
- Wrote an outcome-focused [product spec](spec.md), [design notes](design.md), and [threat model](threat-model.md).
- Implemented the scanner, Markdown/JSON/HTML reports, and a CI-friendly severity threshold using Python's standard library.
- Added safe and deliberately unsafe synthetic customer profiles and shareable report examples.
- Added 21 standard-library tests and a repeatable 12-profile synthetic evaluation; all 28 seeded rule instances were detected in the recorded run.

## Result

**The local suite passed 21/21 tests.** The safe example scored 100/100 and returned **READY TO REVIEW**. The risky example was **BLOCKED** and surfaced cross-tenant write access and fail-open behavior as critical findings. The synthetic evaluation detected all 28 seeded rule instances (28/28); this is evidence of implementation coverage only, not an external security result.

## Value demonstrated

BoundaryCheck demonstrates a full delivery loop: interpret customer-facing role requirements, define scope, choose a low-friction interface, make findings explainable, test failure cases, measure against explicit fixtures, and hand off with limits documented. It shows a path from risk discussion to an artifact that an engineer can run locally and a reviewer can inspect.

## Limitations

The scanner checks declared profile fields only. It cannot inspect or prove runtime controls, discover cloud resources, reason over arbitrary architecture, provide legal/compliance assurance, or certify a launch. The rules need customer security-owner approval before real adoption.

## Recommended next steps for a real pilot

1. Agree with one customer on the profile contract and the meaning of each finding.
2. Compare the profile with deployed identity, network, logging, and tool enforcement settings.
3. Run independent review of false positives and missed risks.
4. Add an exception owner and expiry workflow only after governance is agreed.
5. Measure review time, blocker resolution time, and post-launch incident/rollback signals.
