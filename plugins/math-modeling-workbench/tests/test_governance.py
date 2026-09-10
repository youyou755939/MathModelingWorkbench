#!/usr/bin/env python3
"""Behavioral smoke tests for role ownership and model-freeze enforcement."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import model_freeze  # noqa: E402


def run(script: str, *arguments: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if completed.returncode != expect:
        raise AssertionError(
            f"{script} returned {completed.returncode}, expected {expect}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def write_sources(project: Path) -> None:
    reports = project / "reports"
    reports.mkdir(parents=True)
    (reports / "TASK_CONTRACT.md").write_text("# Contract\nQ1 demand forecast\n", encoding="utf-8")
    (reports / "ANALYSIS_MODELING_REPORT.md").write_text("# Model\nRidge baseline\n", encoding="utf-8")
    (reports / "INPUT_INVENTORY.md").write_text("# Inputs\ndata.csv\n", encoding="utf-8")


def complete_contract(project: Path) -> None:
    path = project / model_freeze.FREEZE_RELATIVE
    data = json.loads(path.read_text(encoding="utf-8"))
    data["global_decisions"] = {
        "data_scope": "all validated rows in data.csv",
        "sampling_unit": "customer",
        "missing_data_policy": "training-fold median imputation",
        "random_seed": 20260910,
        "numeric_tolerance": 1e-8,
    }
    data["questions"][0].update(
        {
            "objective": "forecast next-period demand",
            "model_family": "ridge regression",
            "inputs": ["lagged demand", "calendar indicators"],
            "outputs": ["point forecast", "prediction interval"],
            "fixed_parameters": {"alpha": 1.0},
            "selection_rules": [],
            "constraints": ["training rows precede validation rows"],
            "solver": {
                "name": "closed-form ridge solver",
                "settings": {"fit_intercept": True},
                "stopping_rule": "single deterministic solve",
            },
            "validation": {
                "baseline": "seasonal naive forecast",
                "metrics": ["MAE", "interval coverage"],
                "split_strategy": "rolling-origin split by customer",
                "sensitivity": ["alpha in {0.5, 1.0, 2.0}"],
                "acceptance_criteria": ["MAE no worse than baseline", "coverage at least 90%"],
            },
            "failure_policy": "report failure and do not publish headline metrics",
        }
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_freeze_and_certificate(root: Path) -> None:
    project = root / "freeze-project"
    project.mkdir()
    write_sources(project)
    run(
        "model_freeze.py",
        str(project),
        "init",
        "--problem-id",
        "demo-2026-q1",
        "--title",
        "Demand planning",
        "--question",
        "Q1",
    )
    run("model_freeze.py", str(project), "seal", expect=1)
    complete_contract(project)
    sealed = json.loads(run("model_freeze.py", str(project), "seal").stdout)
    assert len(sealed["sha256"]) == 64
    run("model_freeze.py", str(project), "accept", "--role", "3coding-visual")
    run("model_freeze.py", str(project), "check", "--receipt-role", "3coding-visual")

    run("model_freeze.py", str(project), "revise", "--reason", "increase ridge penalty")
    freeze_path = project / model_freeze.FREEZE_RELATIVE
    revised = json.loads(freeze_path.read_text(encoding="utf-8"))
    revised["questions"][0]["fixed_parameters"]["alpha"] = 2.0
    freeze_path.write_text(json.dumps(revised, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resealed = json.loads(run("model_freeze.py", str(project), "seal").stdout)
    assert resealed["revision"] == 2 and resealed["sha256"] != sealed["sha256"]
    run("model_freeze.py", str(project), "check", "--receipt-role", "3coding-visual", expect=1)
    run("model_freeze.py", str(project), "accept", "--role", "3coding-visual")

    analysis_path = project / "reports" / "ANALYSIS_MODELING_REPORT.md"
    analysis_text = analysis_path.read_text(encoding="utf-8")
    analysis_path.write_text(analysis_text + "changed after freeze\n", encoding="utf-8")
    run("model_freeze.py", str(project), "check", expect=1)
    analysis_path.write_text(analysis_text, encoding="utf-8")
    run("model_freeze.py", str(project), "check", "--receipt-role", "3coding-visual")

    certificate = {
        "problem_id": "demo-2026-q1",
        "model_freeze_revision": resealed["revision"],
        "model_freeze_sha256": resealed["sha256"],
        "run_command": "python code/main.py",
        "exit_code": 0,
        "metrics": [{"name": "MAE", "value": 1.25, "unit": "units"}],
        "hard_constraints": [{"name": "split leakage", "residual": 0, "tolerance": 0, "unit": "rows"}],
        "comparisons": [],
    }
    certificate_path = project / "validation_certificate.json"
    certificate_path.write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    run(
        "validate_result_certificate.py",
        str(certificate_path),
        "--freeze",
        str(freeze_path),
    )
    certificate["model_freeze_sha256"] = "0" * 64
    certificate_path.write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    run(
        "validate_result_certificate.py",
        str(certificate_path),
        "--freeze",
        str(freeze_path),
        expect=1,
    )

    untampered = freeze_path.read_text(encoding="utf-8")
    tampered = json.loads(untampered)
    tampered["questions"][0]["fixed_parameters"]["alpha"] = 3.0
    freeze_path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run("model_freeze.py", str(project), "check", expect=1)


def test_role_state(root: Path) -> None:
    project = root / "state-project"
    reports = project / "reports"
    reports.mkdir(parents=True)
    inventory = reports / "INPUT_INVENTORY.md"
    freeze = reports / "MODEL_FREEZE.json"
    inventory.write_text("inputs\n", encoding="utf-8")
    freeze.write_text("{}\n", encoding="utf-8")
    run("manage_workflow_state.py", str(project), "init")
    run(
        "manage_workflow_state.py",
        str(project),
        "set",
        "intake",
        "complete",
        "--actor",
        "2analysis-modeling",
        "--artifact",
        "reports/INPUT_INVENTORY.md",
        expect=2,
    )
    run(
        "manage_workflow_state.py",
        str(project),
        "set",
        "intake",
        "complete",
        "--actor",
        "1start-mathmodel",
        "--artifact",
        "reports/INPUT_INVENTORY.md",
    )
    run(
        "manage_workflow_state.py",
        str(project),
        "set",
        "coding",
        "complete",
        "--actor",
        "3coding-visual",
        "--artifact",
        "reports/MODEL_FREEZE.json",
        expect=2,
    )
    run(
        "manage_workflow_state.py",
        str(project),
        "set",
        "analysis",
        "complete",
        "--actor",
        "2analysis-modeling",
        "--artifact",
        "reports/MODEL_FREEZE.json",
    )
    run("manage_workflow_state.py", str(project), "audit", "--require-through", "analysis")
    freeze.write_text('{"changed": true}\n', encoding="utf-8")
    run("manage_workflow_state.py", str(project), "audit", expect=1)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mathmodel-governance-") as temporary:
        root = Path(temporary)
        test_freeze_and_certificate(root)
        test_role_state(root)
    print("PASS governance behavior")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
