# Threat model

## Goal and boundary

BoundaryCheck helps a delivery team review a declared AI deployment profile before launch. It is a local policy linter. It does **not** connect to cloud accounts, execute tools, inspect runtime traffic, verify the truth of a profile, or protect the deployment itself.

## Assets and actors

| Item | Concern |
| --- | --- |
| Customer data and prompts | May be exposed by broad tool scope or retained logs |
| Credentials | May be committed to config or copied into reports |
| Customer tenants | Must remain isolated from one another |
| Security review evidence | Should be accurate, attributable, and stored appropriately |
| Engineer / reviewer | Needs readable evidence and a safe way to interpret findings |

Actors include a deployment engineer, customer security reviewer, workflow user, AI application/tool, and a malicious or compromised prompt source.

## Main abuse cases

| Threat | Prototype signal | Residual risk |
| --- | --- | --- |
| Prompt injection induces a broad or harmful tool action | Write tools require approval; global scope is critical | The profile can lie; runtime authorization must enforce scope |
| One tenant reads another tenant's records | Per-customer isolation and tool scope are checked | Scanner does not inspect databases, queries, or identity claims |
| Prompt or personal data persists in telemetry | Prompt logging and redaction fields are checked | Other logs, traces, backups, or provider retention are out of scope |
| Compromised component exfiltrates data | Wildcard outbound access is flagged | Actual firewall policy and DNS behavior are not inspected |
| Auth or policy dependency fails open | Explicit fail-closed field is required | Correct failover behavior must be demonstrated in integration tests |
| Credential leaks through profile/report | Profile should name a managed source, not include secret values | Arbitrary secret scanning is out of scope; report evidence can be sensitive |
| Unsafe change ships without recovery | Rollback confirmation and evaluation fields are checked | Recovery time and production rollback are not exercised here |

## Controls in the demo

- No network access or credential access in the scanner.
- JSON parsing accepts data; no Python evaluation, templating, or shell execution.
- Rule findings cite evidence and paths, and HTML output escapes user-controlled text.
- No automatic tool execution or remediation.
- Synthetic examples and a clear non-certification disclaimer.

## Safe usage guidance

Do not put secrets, live prompts, tokens, hostnames that reveal private infrastructure, or production customer data in a profile. Treat generated reports as potentially sensitive. Review every rule against customer policy before acting on the status.
