# Result certificate schema

Write `code/outputs/validation_certificate.json` after the final run:

```json
{
  "problem_id": "contest-year-problem",
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

Use source level A for official facts or direct attachment-derived invariants, B for independently reproduced/cross-checked results, and C for a single unverified public claim. Set `commensurable` to false when definitions, units, horizon, data, constraints, or accounting differ. Never manufacture a relative error for an incommensurable comparison.

Residuals are signed or unsigned scalar violation magnitudes; the validator checks `abs(residual) <= tolerance`. Record at least all constraints that can invalidate the headline conclusion. For an optimization model, include capacity/balance, domain/integrality, linking/logical, temporal, and problem-specific constraints. For numerical simulation, include conservation/geometric residuals and a mesh/time-step convergence metric. For statistical models, include split leakage checks and coverage/error requirements.
