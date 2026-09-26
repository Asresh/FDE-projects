# Product specification

## Customer problem

An AI team has a working pilot and needs to decide whether it is ready for a customer environment. The details that decide readiness—identity, tenant scope, network access, logging, tool permissions, evaluation, and rollback—are spread across design notes and config. A reviewer needs a quick, repeatable way to see the gaps without reading every file or handing credentials to another service.

## Product

BoundaryCheck is a local command-line profile linter. It accepts a JSON summary of an AI deployment, checks a small transparent policy set, and produces a prioritized report in Markdown, JSON, or HTML. It never connects to the customer environment or executes an agent tool.

## Users and jobs to be done

| User | Need |
| --- | --- |
| Customer-facing engineer | Find launch blockers and show the evidence quickly |
| Customer security reviewer | Review identity, boundaries, data handling, and operational controls |
| Product / operations lead | Agree on a clear owner and acceptance bar before rollout |
| Hiring manager | See end-to-end delivery judgment, implementation, and honest validation evidence |

## Requirements

1. Read one local JSON profile and reject malformed or structurally unsafe input clearly.
2. Check identity, tenant isolation, egress, prompt logging, redaction, tools, failure behavior, secrets, TLS, audit, evaluation, and rollback.
3. Show deterministic severity, rule ID, evidence path, observed value, plain-language reason, and practical recommendation.
4. Produce Markdown, JSON, and standalone HTML without external dependencies.
5. Allow CI to return a non-zero status at a user-selected severity threshold.
6. Include safe and deliberately unsafe synthetic examples and reproducible tests.
7. Never read environment variables, contact a network, or execute user-provided content.

## Success measures for this prototype

- 100% of seeded risky conditions in the 12-profile synthetic fixture set are detected by at least one intended rule.
- The safe example has zero critical/high findings.
- All findings include evidence and a remediation.
- Repeated scans of the same profile produce byte-stable JSON output.
- The full test suite runs with Python's standard library only.

These are prototype acceptance goals, not industry-wide security benchmarks.

## Out of scope

Live cloud discovery, vulnerability scanning, penetration testing, policy-as-code customization, compliance attestation, model quality certification, secret detection in arbitrary files, and automatic remediation. This tool cannot prove that a deployment is safe.

## Assumptions and open questions for a real customer

- Customer owners approve the meaning of each profile field and policy threshold.
- Tool actions are declared accurately and scoped by the actual authorization layer.
- Privacy and retention requirements vary by workflow and jurisdiction.
- A production integration would need signed/versioned profiles, rule governance, exceptions with expiry, and access-controlled evidence storage.
