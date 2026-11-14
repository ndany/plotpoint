# T3c probes, re-run after the fixes they prompted

The tester's 24 probe headlines, re-checked with the revised headline-number
check (D-23, entity-aware matching). "Before" is the tester's result.

| Probe | Kind | Should | Before | After |
| --- | --- | --- | --- | --- |
| P1 | Year-over-year change presented as the renovation drop | fail | pass | pass (window; see note) |
| P4 | Peak-to-latest presented as the renovation drop | fail | pass | pass (window; see note) |
| P9 | Multiple ("8 times") | fail | pass | fail |
| P10 | Another branch's value | fail | pass | fail |
| P11 | Riverside's value attributed to Central | fail | pass | fail |
| P13 | Wrong share in a table | fail | pass | fail |
| P14 | Year inside a word ("FY27") | fail | pass | pass (labels aren't checked; documented) |
| P17 | Quantile share with the wrong threshold | fail | pass | fail |
| P5, P5b | True share on a line chart | pass | fail | pass |
| P24 | True multiple | pass | pass | fail (multiples aren't checkable; state both values) |
| Others | Wrong direction, wrong rounding, values not in the data, wrong counts, distribution claims | as expected | as expected | as expected |

Note: P1 and P4 match a real change over a different window. The check reports
the window it matched; SKILL.md render step 4 tells the model to confirm it is
the one the sentence means.
