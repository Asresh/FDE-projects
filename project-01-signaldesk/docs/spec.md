# Product specification

## Customer situation

The fictional customer is a small software-as-a-service operations team. During an incident, an on-call engineer checks the alert feed, service ownership list, change log, and runbooks separately. That context switching delays the first useful decision, especially overnight. The project demonstrates discovery and a narrow, testable first release; it does not claim the workflow was observed at a real customer.

## Users and needs

| User | Need | Why |
| --- | --- | --- |
| On-call engineer | See a concise incident brief with cited context | Reduce tab switching while keeping control |
| Service owner | Be correctly identified from the catalog | Route questions to the team that knows the system |
| Team lead | Understand recommendation quality and limits | Decide whether a deeper integration pilot is worthwhile |

## Product objective

For a small operations team, turn a synthetic alert plus a small service catalog, recent-change feed, and runbook set into an evidence-linked, read-only triage brief that a human can review in seconds.

## Acceptance criteria

1. An operator can open a local web page and select an incident.
2. Each known incident has a severity, service owner, tier, matching runbooks, and recent changes when available.
3. Each matching suggestion explains which terms matched and includes a source identifier.
4. Weak evidence is labeled as uncertain and prompts the user to gather context.
5. The user can approve, dismiss, or request more context; the demo records the choice for the current process only.
6. The system exposes a health endpoint and JSON API for integration.
7. Automated tests cover core ranking, missing incidents, API behavior, and review safety.
8. A new engineer can start the demo using only Python 3.11+.

## Success measures for this prototype

- 3/3 seeded incident scenarios return the expected runbook first.
- 100% of returned evidence cards include a source.
- Unknown IDs return a 404 response instead of invented details.
- No code path executes remediation.
- From clone to first local page requires one command and no secrets.

These are prototype acceptance targets over tiny invented fixtures. They are not a production SLA or customer outcome claim.

## Scope

**Included:** synthetic feed adapters, small deterministic retrieval, confidence and evidence, operator page, HTTP/JSON interface, demo review records, test suite, container path, deployment notes, and final report.

**Not included:** live integrations, real customer data, authentication, multi-tenant access, persistent database, production observability, LLM calls, automated remediation, incident paging, compliance certification, or 24/7 support.

## Open questions for a real discovery session

- Which incident source is authoritative, and how often does it update?
- How are service ownership and escalation paths represented today?
- Which actions are guidance versus actions a human can approve in the product?
- What should never be sent to an external model or stored in logs?
- Which two incident classes have the highest operational cost?
- What is the baseline time-to-triage and what target would be valuable?
- How should teams measure a correct recommendation when runbooks are stale?

