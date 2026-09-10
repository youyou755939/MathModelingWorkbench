# Result certificate schema

Write `code/outputs/validation_certificate.json` after the final run:

```json
{
  "problem_id": "contest-year-problem",
  "model_freeze_revision": 1,
  "model_freeze_sha256": "64-character SHA-256 from MODEL_FREEZE.json",
  "run_command": "python code/main.py",
  "exit_code": 0,
  "metrics": [
    {"name": "objective", "value": 123.4, "unit": "yuan"}
  ],
  "hard_constraints": [
    {"name": "capacity excess", "residual": 0.0, "tolerance": 1e-7, "unit": "mu"}
  ],
  "comparisons": [
    {
      "label": "independently reproduced public result",
      "source_level": "B",
      "metric": "objective",
      "unit": "yuan",
      "accounting_horizon": "2024-2030 total",
      "hard_constraint_status": "PASS",
      "current_value": 123.4,
      "reference_value": 120.0,
      "commensurable": true
    }
  ]
}
```

The two freeze fields are mandatory. Copy them from the successful output of `model_freeze.py <project> check`; do not recompute them from an unsealed draft. Validate the certificate with `--freeze reports/MODEL_FREEZE.json`. If the freeze or its source artifacts change, the certificate is stale and the final run must be repeated under the new revision.

Use source level A for official facts or direct attachment-derived invariants, B for independently reproduced/cross-checked results, and C for a single unverified public claim. Set `commensurable` to false when definitions, units, horizon, data, constraints, or accounting differ. Never manufacture a relative error for an incommensurable comparison.

Residuals are signed or unsigned scalar violation magnitudes; the validator checks `abs(residual) <= tolerance`. Record at least all constraints that can invalidate the headline conclusion. For an optimization model, include capacity/balance, domain/integrality, linking/logical, temporal, and problem-specific constraints. For numerical simulation, include conservation/geometric residuals and a mesh/time-step convergence metric. For statistical models, include split leakage checks and coverage/error requirements.
