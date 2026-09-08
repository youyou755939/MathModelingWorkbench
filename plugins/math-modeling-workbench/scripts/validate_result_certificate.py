#!/usr/bin/env python3
"""Validate a model-result certificate and compute commensurable errors."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mathematical-model result evidence")
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--out", type=Path, help="write normalized validation summary")
    args = parser.parse_args()

    data = json.loads(args.certificate.read_text(encoding="utf-8"))
    failures: list[str] = []
    warnings: list[str] = []

    for key in ("problem_id", "run_command", "exit_code", "metrics", "hard_constraints", "comparisons"):
        if key not in data:
            failures.append(f"missing required field: {key}")
    if data.get("exit_code") != 0:
        failures.append(f"reproduction command exit_code={data.get('exit_code')}")

    for i, metric in enumerate(data.get("metrics", [])):
        if not metric.get("name") or not metric.get("unit"):
            failures.append(f"metrics[{i}] needs name and unit")
        if not finite_number(metric.get("value")):
            failures.append(f"metrics[{i}].value is not finite")

    normalized_constraints = []
    for i, check in enumerate(data.get("hard_constraints", [])):
        residual = check.get("residual")
        tolerance = check.get("tolerance")
        if not finite_number(residual) or not finite_number(tolerance) or tolerance < 0:
            failures.append(f"hard_constraints[{i}] needs finite residual and nonnegative tolerance")
            continue
        passed = abs(residual) <= tolerance
        normalized_constraints.append({**check, "passed": passed})
        if not passed:
            failures.append(f"hard constraint failed: {check.get('name', i)} ({residual} > {tolerance})")

    normalized_comparisons = []
    required = ("label", "source_level", "metric", "unit", "accounting_horizon", "hard_constraint_status")
    for i, comp in enumerate(data.get("comparisons", [])):
        missing = [k for k in required if not comp.get(k)]
        if missing:
            failures.append(f"comparisons[{i}] missing: {', '.join(missing)}")
            continue
        if comp["source_level"] not in {"A", "B", "C"}:
            failures.append(f"comparisons[{i}].source_level must be A, B or C")
        commensurable = bool(comp.get("commensurable", False))
        item = dict(comp)
        if commensurable:
            current = comp.get("current_value")
            reference = comp.get("reference_value")
            if not finite_number(current) or not finite_number(reference):
                failures.append(f"comparisons[{i}] commensurable values must be finite")
            elif comp["hard_constraint_status"] != "PASS":
                failures.append(f"comparisons[{i}] cannot be commensurable when reference constraints do not PASS")
            else:
                item["absolute_error"] = current - reference
                item["relative_error"] = None if reference == 0 else (current - reference) / abs(reference)
        else:
            warnings.append(f"comparison not commensurable: {comp['label']}")
        normalized_comparisons.append(item)

    if not data.get("hard_constraints"):
        failures.append("no hard constraints recorded")
    result = {
        "problem_id": data.get("problem_id"),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "warnings": warnings,
        "hard_constraints": normalized_constraints,
        "comparisons": normalized_comparisons,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
