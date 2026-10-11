# DIVA-SQL evaluation summary

## bird (questions answered by all systems: 200)

| System | n | EX | 95% CI | mean latency (s) | LLM calls / q | tokens / q |
|---|---|---|---|---|---|---|
| diva | 200 | 36.0% | 29.3–42.7% | 100.97 | 17.6 | 34988 |
| plain | 200 | 40.0% | 33.2–46.8% | 8.13 | 1.0 | 2084 |

Accuracy by query category (EX, n in brackets):

| System | simple_selection | single_join | multiple_joins | aggregation | nested |
|---|---|---|---|---|---|
| diva | 57.9% (19) | 34.5% (113) | 36.4% (33) | 16.7% (24) | 54.5% (11) |
| plain | 42.1% (19) | 39.8% (113) | 45.5% (33) | 29.2% (24) | 45.5% (11) |

McNemar's test against DIVA-SQL (b = DIVA-SQL correct and other wrong; c = the reverse):

| Comparison | b | c | chi² | p | method |
|---|---|---|---|---|---|
| DIVA-SQL vs plain | 16 | 24 | 1.23 | 2.68e-01 | chi-square with continuity correction |

DIVA-SQL pipeline status counts: {'SUCCESS': 191, 'PARTIAL_SUCCESS': 9}
Median semantic-DAG size: 4 nodes
Questions where at least one clause failed verification: 165

## spider (questions answered by all systems: 200)

| System | n | EX | 95% CI | mean latency (s) | LLM calls / q | tokens / q |
|---|---|---|---|---|---|---|
| diva | 200 | 72.0% | 65.8–78.2% | 76.26 | 14.5 | 24667 |
| plain | 200 | 76.0% | 70.1–81.9% | 3.42 | 1.0 | 790 |

Accuracy by query category (EX, n in brackets):

| System | simple_selection | single_join | multiple_joins | aggregation | nested |
|---|---|---|---|---|---|
| diva | 83.6% (55) | 69.0% (58) | 33.3% (9) | 74.0% (50) | 64.3% (28) |
| plain | 85.5% (55) | 70.7% (58) | 77.8% (9) | 76.0% (50) | 67.9% (28) |

McNemar's test against DIVA-SQL (b = DIVA-SQL correct and other wrong; c = the reverse):

| Comparison | b | c | chi² | p | method |
|---|---|---|---|---|---|
| DIVA-SQL vs plain | 9 | 17 | 1.88 | 1.70e-01 | chi-square with continuity correction |

DIVA-SQL pipeline status counts: {'SUCCESS': 191, 'PARTIAL_SUCCESS': 8, 'FAILURE': 1}
Median semantic-DAG size: 3 nodes
Questions where at least one clause failed verification: 145
