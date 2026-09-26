# Final submission report — SignalDesk

## Executive summary

SignalDesk is a local-first incident triage prototype built around a fictional SaaS operations workflow. It brings an alert, service ownership, recent changes, and runbook evidence into one brief. The operator can inspect the sources and record a review decision. The prototype cannot execute remediation, and the included data is synthetic.

## Delivery summary

| Workstream | Delivered |
| --- | --- |
| Discovery and specification | Fictional customer problem, user needs, acceptance criteria, success measures, and discovery questions |
| Design | Data contracts, explainable keyword retrieval, confidence caveats, HTTP routes, and privacy/deployment boundary |
| Build | Python service, local JSON API, responsive operator page, synthetic fixtures, and Dockerfile |
| Test | 12 standard-library unit/integration/negative/safety checks plus a 3-case golden set |
| Evaluation | Acceptance results with explicit warning that the small hand-built set does not prove general quality |
| Enablement | One-command run guide, diagrams, role research, API examples, and operator-oriented explanation |

## Acceptance review

- Operator can select an incident and see a triage brief: **met**.
- Brief includes owner, service tier, ranked runbooks, recent changes, and source-linked evidence: **met for all seeded incidents**.
- Weak matches provide an uncertainty path; unknown records return 404: **met**.
- Review decisions are limited to approve, dismiss, or request more context: **met**.
- Health and JSON endpoints are available: **met**.
- Tests can be run without packages or secrets: **met**.

## Test outcome

The baseline suite contains 13 test methods. It passes against the checked-in synthetic dataset, including one explicit regression check across all three expected runbook matches. The repeatable command is:

```bash
python3 -m unittest discover -s tests -v
```

## What the work demonstrates

The project shows how an FDE can take a customer-shaped problem from scoping through an implemented workflow and a reviewable validation plan. The core strength is end-to-end ownership and clear handoff: a reviewer can run the demo, inspect each input, trace each recommendation, and understand the limitations without an API key.

## Known limitations

- No real customer discovery or user research was conducted.
- Synthetic examples are too small and too self-consistent to estimate real-world recall or precision.
- Keyword matching misses synonyms and complex symptoms.
- Data is read from static files; no freshness, authentication, tenancy, persistence, or production monitoring is provided.
- Browser layout is manually designed but has not had an automated accessibility audit.
- No measured latency or uptime claim is made.

## Recommended next step for a customer pilot

Run a two-week discovery and shadow-mode pilot with one service team. Connect one read-only incident source and one service catalog through customer-approved credentials, select 20–50 de-identified historical cases, and have operators label useful context and top runbook. Agree the data boundary, baseline time-to-triage, relevance threshold, and escalation policy before showing suggestions in a live workflow. Keep recommendations read-only until the team validates quality and access controls.

## Reproduction checklist

1. Install Python 3.11 or newer.
2. Run `python3 -m signaldesk` and open `http://127.0.0.1:8000`.
3. Select each sample incident and trace the sources in its brief.
4. Record a review choice; restart the process and observe that the demo record is transient.
5. Run `python3 -m unittest discover -s tests -v`.
