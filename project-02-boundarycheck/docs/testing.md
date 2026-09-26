# Test plan and observed results

## How to run

```bash
python3 -m unittest discover -s tests -v
```

The suite uses only Python's standard library. It covers the scanner and command-line workflow using temporary files; it does not contact a network or customer environment.

## Cases

| ID | Case | Expected behavior |
| --- | --- | --- |
| T01 | Safe support profile | `READY TO REVIEW`, zero findings |
| T02 | Non-object JSON root | Raise a clear `ProfileError` |
| T03 | Wrong egress field type | Reject profile rather than silently skip a check |
| T04 | Unsupported / missing authentication | Emit `BC001` high |
| T05 | Shared tenant boundary | Emit `BC002` high |
| T06 | Prompt retention enabled | Emit `BC003` high |
| T07 | Sensitive-field redaction disabled | Emit `BC004` medium |
| T08 | Wildcard egress | Emit `BC005` high |
| T09 | Write tool without approval | Emit `BC006` high |
| T10 | Tool with all-tenant scope | Emit `BC007` critical |
| T11 | Fail-open policy | Emit `BC008` critical |
| T12 | Unmanaged secret source | Emit `BC009` high |
| T13 | TLS disabled | Emit `BC010` high |
| T14 | Audit events disabled | Emit `BC011` medium |
| T15 | Missing/invalid evaluation bar and no rollback | Emit `BC012`, `BC013`, `BC014` |
| T16 | Finding order and score | Stable severity ordering and repeatable score |
| T17 | HTML special characters in customer label | Render escaped text, not an HTML tag |
| T18 | CLI output and threshold | Writes report and returns 1 when configured threshold is met |
| T19 | CLI malformed JSON | Returns 2 with readable error |
| T20 | CLI missing profile | Returns 2 with readable error |

## Observed run

**Result: 21 tests passed.** The command above completed successfully in the local Python 3.9 runtime used for this submission. The tests are not an independent security audit and do not validate any live environment.

The safe fixture produced **READY TO REVIEW**, score **100/100**, and zero findings. The deliberately risky fixture produced **BLOCKED**, with critical/high issues including `BC007` for a cross-tenant write tool and `BC008` for fail-open behavior. See [`../reports/retail-risk-review.html`](../reports/retail-risk-review.html) and [`../reports/retail-risk-review.json`](../reports/retail-risk-review.json) for example artifacts.
