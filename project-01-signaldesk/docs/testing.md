# Test plan and executed cases

## How to run

From the project directory:

```bash
python3 -m unittest discover -s tests -v
```

The suite uses only Python's built-in `unittest` module. It runs without network access, credentials, or a test database.

## Case catalogue

| ID | Type | Scenario | Expected result |
| --- | --- | --- | --- |
| ENG-01 | Unit | P1 database pool saturation incident | Commerce Platform owner, `RB-017`, and `CHG-882` appear |
| ENG-02 | Unit | Search indexing lag incident | `RB-023` is top ranked; matching terms explain why |
| ENG-03 | Regression | Each of the three seeded incidents is compared with its expected runbook | Expected runbook is ranked first for all 3 cases |
| ENG-04 | Unit | Incident ID does not exist | Engine returns no result |
| ENG-05 | Unit | Public incident summary is built | Internal query-only symptom field is omitted |
| ENG-06 | Safety | Every synthetic incident is triaged | Brief says it does not execute remediation and evidence has source labels |
| API-01 | Integration | Liveness endpoint | `200`, status `ok` |
| API-02 | Integration | Incident list | `200`, JSON media type, 3 records |
| API-03 | Integration | Known incident detail | `200`; every evidence item has a source |
| API-04 | Negative | Unknown incident detail | `404`, `incident_not_found` |
| API-05 | Integration | Allowed review decision | `201`; note and decision recorded in the process |
| API-06 | Safety | Unsupported `execute_fix` review decision | `400`, allowed review values returned |
| API-07 | Negative | Review references unknown incident | `404`, no decision stored |

## Executed result

The recorded baseline for this project is **13 test methods, all passing**. Run the command above to reproduce the result in your environment. The tests are deterministic and read only the repository's synthetic fixture files.

## Useful additions before production

- Property-based tests for malformed and incomplete customer records.
- Contract tests against the real incident and service catalog APIs.
- Security tests for authentication, authorization, tenant isolation, and audit fields.
- Offline relevance evaluation on customer-approved and de-identified historical examples.
- Load and soak tests against a production-sized data volume.
- Browser-based accessibility and responsive layout checks.
- Fault-injection tests for source system timeouts and stale runbooks.
