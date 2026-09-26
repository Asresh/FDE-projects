# Prototype evaluation

## Method

Run `python3 scripts/evaluate.py` to build and scan 12 synthetic deployment profiles from the safe example. Each profile has expected rule IDs defined before the scan. A true positive is an expected rule appearing; a false negative is an expected rule missing. Because labels were written from the same policy spec, this is a plumbing/coverage check, not independent validation of the policy itself.

## Results

| Measure | Observed |
| --- | ---: |
| Profiles in the fixture set | 12 |
| Seeded rule instances | 28 |
| Expected rule instances detected | 28 / 28 (100%) |
| Seeded rule instances missed | 0 |
| Safe profile critical/high findings | 0 |
| Findings with path, evidence, and recommendation | 100% |
| Repeated JSON scans stable | Yes |

## Interpretation

The checked-in run observed all 28 seeded rule instances across 12 fixtures (100% coverage within this small synthetic set). The rules detect the risky settings they were designed to detect in these fixtures. That supports using the tool as an explainable checklist starter. It does **not** mean the policy set is complete, profiles match reality, or a passing deployment is secure. Broader validation would require independent customer security review, more varied profiles, and integration tests against the actual identity, network, logging, and tool enforcement layers.

## Next evaluation step

With a real pilot team, collect de-identified profile examples, ask reviewers to label them independently, measure agreement and false alarms, and update rule wording before adjusting thresholds. Track time-to-review and blocker resolution as customer outcomes rather than optimizing only for a score.
