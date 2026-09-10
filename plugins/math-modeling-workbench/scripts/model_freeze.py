#!/usr/bin/env python3
"""Create, seal, verify, accept, and revise a mathematical-model contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
FREEZE_RELATIVE = Path("reports/MODEL_FREEZE.json")
RECEIPT_DIR = Path("reports/model-freeze-receipts")
ROLES = ("3coding-visual", "4drawio", "5writing", "6verity")
REQUIRED_SOURCES = {
    "task_contract": "reports/TASK_CONTRACT.md",
    "analysis_report": "reports/ANALYSIS_MODELING_REPORT.md",
    "input_inventory": "reports/INPUT_INVENTORY.md",
}
PLACEHOLDER = re.compile(r"(?i)(?:\bTODO\b|\bTBD\b|__REQUIRED__|待定|待补|占位|<[^>]+>)")


class FreezeError(RuntimeError):
    """Raised when a freeze contract or receipt is invalid."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="model-freeze-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_digest(data: dict[str, Any]) -> str:
    payload = dict(data)
    payload.pop("seal", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"cannot read JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FreezeError(f"expected a JSON object: {path}")
    return data


def project_file(project: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise FreezeError("source artifact path must be a non-empty string")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise FreezeError(f"source artifact must use a project-relative path: {relative}")
    resolved = (project / candidate).resolve()
    if not resolved.is_relative_to(project) or not resolved.is_file():
        raise FreezeError(f"source artifact is missing or outside project: {relative}")
    return resolved


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and PLACEHOLDER.search(value) is None


def nonempty_text_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_text(item) for item in value)


def complete_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return nonempty_text(value)
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return bool(value) and all(complete_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(nonempty_text(key) and complete_value(item) for key, item in value.items())
    return isinstance(value, (bool, int))


def scan_placeholders(value: object, path: str = "$.") -> list[str]:
    failures: list[str] = []
    if isinstance(value, str) and PLACEHOLDER.search(value):
        failures.append(f"placeholder text at {path}")
    elif isinstance(value, dict):
        for key, item in value.items():
            if key != "seal":
                failures.extend(scan_placeholders(item, f"{path}{key}."))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(scan_placeholders(item, f"{path}[{index}]."))
    return failures


def validate_content(data: dict[str, Any], project: Path) -> list[str]:
    failures: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data.get("revision"), int) or isinstance(data.get("revision"), bool) or data["revision"] < 1:
        failures.append("revision must be a positive integer")
    if not nonempty_text(data.get("freeze_id")):
        failures.append("freeze_id is required")

    problem = data.get("problem")
    if not isinstance(problem, dict):
        failures.append("problem must be an object")
        problem = {}
    for key in ("id", "title"):
        if not nonempty_text(problem.get(key)):
            failures.append(f"problem.{key} is required")
    question_ids = problem.get("question_ids")
    if not nonempty_text_list(question_ids) or len(question_ids) != len(set(question_ids or [])):
        failures.append("problem.question_ids must be a non-empty unique string list")
    expected_freeze_id = f"{problem.get('id')}-r{data.get('revision')}"
    if data.get("freeze_id") != expected_freeze_id:
        failures.append(f"freeze_id must be {expected_freeze_id}")

    sources = data.get("source_artifacts")
    if not isinstance(sources, dict):
        failures.append("source_artifacts must be an object")
        sources = {}
    for key, expected in REQUIRED_SOURCES.items():
        if sources.get(key) != expected:
            failures.append(f"source_artifacts.{key} must be {expected}")
            continue
        try:
            project_file(project, sources[key])
        except FreezeError as exc:
            failures.append(str(exc))

    global_decisions = data.get("global_decisions")
    if not isinstance(global_decisions, dict):
        failures.append("global_decisions must be an object")
        global_decisions = {}
    for key in ("data_scope", "sampling_unit", "missing_data_policy"):
        if not nonempty_text(global_decisions.get(key)):
            failures.append(f"global_decisions.{key} is required")
    seed = global_decisions.get("random_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        failures.append("global_decisions.random_seed must be an integer")
    tolerance = global_decisions.get("numeric_tolerance")
    if (
        not isinstance(tolerance, (int, float))
        or isinstance(tolerance, bool)
        or not math.isfinite(tolerance)
        or tolerance <= 0
    ):
        failures.append("global_decisions.numeric_tolerance must be finite and positive")

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        failures.append("questions must be a non-empty list")
        questions = []
    seen: list[str] = []
    for index, question in enumerate(questions):
        prefix = f"questions[{index}]"
        if not isinstance(question, dict):
            failures.append(f"{prefix} must be an object")
            continue
        identifier = question.get("id")
        if not nonempty_text(identifier):
            failures.append(f"{prefix}.id is required")
        else:
            seen.append(identifier)
        for key in ("objective", "model_family", "failure_policy"):
            if not nonempty_text(question.get(key)):
                failures.append(f"{prefix}.{key} is required")
        for key in ("inputs", "outputs", "constraints"):
            if not nonempty_text_list(question.get(key)):
                failures.append(f"{prefix}.{key} must be a non-empty string list")
        fixed = question.get("fixed_parameters")
        rules = question.get("selection_rules")
        if not isinstance(fixed, dict):
            failures.append(f"{prefix}.fixed_parameters must be an object")
            fixed = {}
        elif fixed and not complete_value(fixed):
            failures.append(f"{prefix}.fixed_parameters contains an unset or invalid value")
        if not isinstance(rules, list) or not all(nonempty_text(item) for item in rules):
            failures.append(f"{prefix}.selection_rules must be a string list")
            rules = []
        if not fixed and not rules:
            failures.append(f"{prefix} needs fixed_parameters or training-only selection_rules")

        solver = question.get("solver")
        if not isinstance(solver, dict):
            failures.append(f"{prefix}.solver must be an object")
            solver = {}
        if not nonempty_text(solver.get("name")):
            failures.append(f"{prefix}.solver.name is required")
        if not isinstance(solver.get("settings"), dict):
            failures.append(f"{prefix}.solver.settings must be an object")
        elif solver["settings"] and not complete_value(solver["settings"]):
            failures.append(f"{prefix}.solver.settings contains an unset or invalid value")
        if not nonempty_text(solver.get("stopping_rule")):
            failures.append(f"{prefix}.solver.stopping_rule is required")

        validation = question.get("validation")
        if not isinstance(validation, dict):
            failures.append(f"{prefix}.validation must be an object")
            validation = {}
        for key in ("baseline", "split_strategy"):
            if not nonempty_text(validation.get(key)):
                failures.append(f"{prefix}.validation.{key} is required")
        for key in ("metrics", "sensitivity", "acceptance_criteria"):
            if not nonempty_text_list(validation.get(key)):
                failures.append(f"{prefix}.validation.{key} must be a non-empty string list")

    if question_ids and seen != question_ids:
        failures.append("questions ids and order must exactly match problem.question_ids")

    control = data.get("change_control")
    if not isinstance(control, dict):
        failures.append("change_control must be an object")
        control = {}
    if control.get("model_owner") != "2analysis-modeling":
        failures.append("change_control.model_owner must be 2analysis-modeling")
    if control.get("implementation_owner") != "3coding-visual":
        failures.append("change_control.implementation_owner must be 3coding-visual")
    if control.get("material_change_requires_reseal") is not True:
        failures.append("change_control.material_change_requires_reseal must be true")
    if not nonempty_text(control.get("revision_reason")):
        failures.append("change_control.revision_reason is required")
    if not isinstance(data.get("change_history"), list):
        failures.append("change_history must be a list")
    failures.extend(scan_placeholders(data))
    return list(dict.fromkeys(failures))


def source_hashes(data: dict[str, Any], project: Path) -> dict[str, str]:
    return {
        key: sha256_file(project_file(project, relative))
        for key, relative in data["source_artifacts"].items()
    }


def freeze_path(project: Path) -> Path:
    return project / FREEZE_RELATIVE


def check_freeze(project: Path, receipt_roles: list[str] | None = None) -> dict[str, Any]:
    project = project.resolve()
    path = freeze_path(project)
    data = load_object(path)
    failures = validate_content(data, project)
    if data.get("status") != "frozen":
        failures.append("status must be frozen")
    seal = data.get("seal")
    if not isinstance(seal, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(seal.get("sha256", ""))):
        failures.append("seal.sha256 is missing or invalid")
        sealed_digest = ""
    else:
        sealed_digest = str(seal["sha256"])
        if canonical_digest(data) != sealed_digest:
            failures.append("freeze content changed after sealing")
    expected_hashes = data.get("source_hashes")
    if not isinstance(expected_hashes, dict):
        failures.append("source_hashes must be an object")
    else:
        try:
            if source_hashes(data, project) != expected_hashes:
                failures.append("a frozen source artifact changed after sealing")
        except FreezeError as exc:
            failures.append(str(exc))

    for role in receipt_roles or []:
        receipt_path = project / RECEIPT_DIR / f"{role}.json"
        try:
            receipt = load_object(receipt_path)
        except FreezeError as exc:
            failures.append(str(exc))
            continue
        if receipt.get("role") != role:
            failures.append(f"receipt role mismatch: {role}")
        if receipt.get("freeze_sha256") != sealed_digest:
            failures.append(f"stale freeze receipt: {role}")
        if receipt.get("freeze_revision") != data.get("revision"):
            failures.append(f"receipt revision mismatch: {role}")

    if failures:
        raise FreezeError("; ".join(dict.fromkeys(failures)))
    return {
        "status": "PASS",
        "freeze": FREEZE_RELATIVE.as_posix(),
        "problem_id": data["problem"]["id"],
        "revision": data["revision"],
        "sha256": sealed_digest,
        "receipt_roles": receipt_roles or [],
    }


def initial_contract(problem_id: str, title: str, question_ids: list[str]) -> dict[str, Any]:
    questions = []
    for identifier in question_ids:
        questions.append(
            {
                "id": identifier,
                "objective": "",
                "model_family": "",
                "inputs": [],
                "outputs": [],
                "fixed_parameters": {},
                "selection_rules": [],
                "constraints": [],
                "solver": {"name": "", "settings": {}, "stopping_rule": ""},
                "validation": {
                    "baseline": "",
                    "metrics": [],
                    "split_strategy": "",
                    "sensitivity": [],
                    "acceptance_criteria": [],
                },
                "failure_policy": "",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "freeze_id": f"{problem_id}-r1",
        "revision": 1,
        "status": "draft",
        "problem": {"id": problem_id, "title": title, "question_ids": question_ids},
        "source_artifacts": dict(REQUIRED_SOURCES),
        "source_hashes": {},
        "global_decisions": {
            "data_scope": "",
            "sampling_unit": "",
            "missing_data_policy": "",
            "random_seed": None,
            "numeric_tolerance": None,
        },
        "questions": questions,
        "change_control": {
            "model_owner": "2analysis-modeling",
            "implementation_owner": "3coding-visual",
            "revision_reason": "initial freeze",
            "material_change_requires_reseal": True,
        },
        "change_history": [],
    }


def seal(project: Path) -> dict[str, Any]:
    path = freeze_path(project)
    data = load_object(path)
    if data.get("status") != "draft":
        raise FreezeError("only a draft freeze can be sealed")
    failures = validate_content(data, project)
    if failures:
        raise FreezeError("; ".join(failures))
    data["source_hashes"] = source_hashes(data, project)
    data["status"] = "frozen"
    data["seal"] = {"sealed_at": now(), "sha256": canonical_digest(data)}
    atomic_write(path, data)
    return check_freeze(project)


def revise(project: Path, reason: str) -> dict[str, Any]:
    checked = check_freeze(project)
    path = freeze_path(project)
    data = load_object(path)
    data["change_history"].append(
        {
            "from_revision": data["revision"],
            "previous_sha256": checked["sha256"],
            "reason": reason,
            "opened_at": now(),
        }
    )
    data["revision"] += 1
    data["freeze_id"] = f"{data['problem']['id']}-r{data['revision']}"
    data["status"] = "draft"
    data["source_hashes"] = {}
    data["change_control"]["revision_reason"] = reason
    data.pop("seal", None)
    atomic_write(path, data)
    return {"status": "DRAFT", "revision": data["revision"], "reason": reason}


def accept(project: Path, role: str) -> dict[str, Any]:
    checked = check_freeze(project)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "role": role,
        "freeze_revision": checked["revision"],
        "freeze_sha256": checked["sha256"],
        "accepted_at": now(),
        "freeze": FREEZE_RELATIVE.as_posix(),
    }
    path = project / RECEIPT_DIR / f"{role}.json"
    atomic_write(path, receipt)
    return {"status": "ACCEPTED", "receipt": path.relative_to(project).as_posix(), **receipt}


def main() -> int:
    parser = argparse.ArgumentParser(description="管理数学建模参数冻结契约")
    parser.add_argument("project_root", type=Path)
    subparsers = parser.add_subparsers(dest="action", required=True)

    init_parser = subparsers.add_parser("init", help="创建不覆盖已有文件的参数冻结草稿")
    init_parser.add_argument("--problem-id", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--question", action="append", required=True, dest="questions")
    subparsers.add_parser("seal", help="校验并封印完整草稿")
    check_parser = subparsers.add_parser("check", help="校验封印、上游文件和可选角色回执")
    check_parser.add_argument("--receipt-role", action="append", choices=ROLES, default=[])
    accept_parser = subparsers.add_parser("accept", help="为当前冻结版本写入角色接受回执")
    accept_parser.add_argument("--role", required=True, choices=ROLES)
    revise_parser = subparsers.add_parser("revise", help="由建模阶段打开下一修订版")
    revise_parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    project = args.project_root.resolve()
    if not project.is_dir():
        parser.error(f"project directory does not exist: {project}")
    try:
        if args.action == "init":
            path = freeze_path(project)
            if path.exists():
                raise FreezeError(f"freeze already exists: {path}")
            if len(args.questions) != len(set(args.questions)):
                raise FreezeError("question ids must be unique")
            atomic_write(path, initial_contract(args.problem_id, args.title, args.questions))
            result = {"status": "DRAFT", "freeze": FREEZE_RELATIVE.as_posix()}
        elif args.action == "seal":
            result = seal(project)
        elif args.action == "check":
            result = check_freeze(project, args.receipt_role)
        elif args.action == "accept":
            result = accept(project, args.role)
        else:
            result = revise(project, args.reason)
    except FreezeError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
