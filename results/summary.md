# DIVA-SQL evaluation summary

## bird (questions answered by all systems: 200)

| System | n | EX | 95% CI | mean latency (s) | LLM calls / q | tokens / q |
|---|---|---|---|---|---|---|
| plain | 200 | 41.0% | 34.2–47.8% | 121.80 | 1.0 | 405 |

Accuracy by query category (EX, n in brackets):

| System | simple_selection | single_join | multiple_joins | aggregation | nested |
|---|---|---|---|---|---|
| plain | 52.6% (19) | 42.5% (113) | 45.5% (33) | 20.8% (24) | 36.4% (11) |

## spider (questions answered by all systems: 200)

| System | n | EX | 95% CI | mean latency (s) | LLM calls / q | tokens / q |
|---|---|---|---|---|---|---|
| plain | 200 | 77.5% | 71.7–83.3% | 8.76 | 1.0 | 204 |

Accuracy by query category (EX, n in brackets):

| System | simple_selection | single_join | multiple_joins | aggregation | nested |
|---|---|---|---|---|---|
| plain | 85.5% (55) | 77.6% (58) | 44.4% (9) | 80.0% (50) | 67.9% (28) |
