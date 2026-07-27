# Repository Instructions

- Keep `mean_observed(values)` compatible.
- Run the focused check first:
  `python -m unittest -q tests.test_metrics_focused`.
- Then run the full smoke check: `python -m unittest -q`.
- Continue after focused success if the smoke check reveals another defect.
