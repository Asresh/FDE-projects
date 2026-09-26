# Prototype evaluation

## Method

The golden set contains three hand-authored synthetic incidents. For each one, the expected runbook is the one that matches the intended symptom group. Unit and API tests assert that the expected runbook ranks first, its matching terms are shown, source evidence is present, unknown records remain unknown, and only allowed human review decisions are accepted.

This is a functional prototype check, not a statistically meaningful model-quality evaluation. The examples were written alongside the rules, so the results are not independent evidence of general accuracy.

## Results

| Measure | Observed result | Interpretation |
| --- | ---: | --- |
| Golden incident cases with expected runbook ranked first | 3 / 3 | The implementation passes its deliberately small acceptance set |
| Incident detail tests | 2 / 2 including unknown-ID behavior | Known records are enriched; missing records are not fabricated |
| Evidence cards with a source label | 100% in seeded examples | Each card can be inspected in the demo |
| Invalid review action accepted | 0 | There is no remediation action in the review vocabulary |
| Automated test methods | 13 / 13 pass in the baseline suite | Core, API, negative, and safety behavior is covered |
| External credentials required | 0 | Local demo can be run without provider keys |

## How to read the confidence

The number shown in the demo is a simple heuristic derived from token overlap. It is useful for demonstrating an uncertainty path but **is not calibrated probability**, and the UI must not be used to automate incident response. The strongest next step is collecting labeled triage decisions with an actual operations team, agreeing a relevance metric, and comparing a transparent baseline with more capable retrieval methods.

## Operational checks

- Default host is `127.0.0.1`.
- `/health` returns a compact liveness response.
- HTTP errors use clear status codes and JSON error names.
- The static UI escapes external strings before inserting them into HTML.
- Decisions disappear when the process stops.

No latency benchmark is reported here: the dataset is tiny and the result would imply more than this local in-memory prototype can support.
