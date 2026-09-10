#!/usr/bin/env python3
"""Initialize and atomically update Math Modeling Workbench stage state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


STAGES = ("intake", "analysis", "coding", "diagram", "writing", "verification")
STATUSES = ("pending", "in_progress", "complete", "failed")
STAGE_OWNERS = {
    "intake": "1start-mathmodel",
    "analysis": "2analysis-modeling",
    "coding": "3coding-visual",
    "diagram": "4drawio",
    "writing": "5writing",
    "verification": "6verity",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_path(project: Path) -> Path:
    return project / "reports" / "WORKFLOW_STATE.json"


def initial_state() -> dict:
    return {
        "schema_version": 1,
        "updated_at": now(),
        "active_stage": "intake",
        "stages": {stage: "pending" for stage in STAGES},
        "stage_records": {},
        "last_verified_artifact": "",
        "recovery_note": "",
    }


def load(path: Path) -> dict:
    if not path.is_file():
        return initial_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("stages"), dict):
        raise ValueError("不支持的工作流状态文件")
    for stage in STAGES:
        status = data["stages"].get(stage)
        if status not in STATUSES:
            raise ValueError(f"非法阶段状态：{stage}={status}")
    if not isinstance(data.get("stage_records", {}), dict):
        raise ValueError("非法阶段记录")
    data.setdefault("stage_records", {})
    return data


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="workflow-state-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
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


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def invalidate_downstream(data: dict, stage: str) -> None:
    for downstream in STAGES[STAGES.index(stage) + 1 :]:
        data["stages"][downstream] = "pending"
        data["stage_records"].pop(downstream, None)


def update_state(
    data: dict,
    stage: str,
    status: str,
    artifact: str,
    artifact_sha256: str,
    note: str,
    actor: str,
) -> dict:
    previous = data["stage_records"].get(stage, {})
    data["stages"][stage] = status
    if status != "complete" or previous.get("artifact_sha256") != artifact_sha256:
        invalidate_downstream(data, stage)
    data["active_stage"] = stage
    if artifact:
        data["last_verified_artifact"] = artifact
    if note:
        data["recovery_note"] = note
    if status == "complete":
        data["stage_records"][stage] = {
            "owner": actor,
            "artifact": artifact,
            "artifact_sha256": artifact_sha256,
            "completed_at": now(),
        }
        index = STAGES.index(stage)
        data["active_stage"] = STAGES[index + 1] if index + 1 < len(STAGES) else "complete"
    else:
        data["stage_records"].pop(stage, None)
    data["updated_at"] = now()
    return data


def audit_state(data: dict, project: Path, require_through: str | None = None) -> list[str]:
    failures = []
    if require_through:
        for stage in STAGES[: STAGES.index(require_through) + 1]:
            if data["stages"][stage] != "complete":
                failures.append(f"{stage}: 尚未完成")
    records = data.get("stage_records", {})
    for stage in STAGES:
        if data["stages"][stage] != "complete":
            continue
        record = records.get(stage)
        if not isinstance(record, dict):
            failures.append(f"{stage}: 缺少完成记录")
            continue
        if record.get("owner") != STAGE_OWNERS[stage]:
            failures.append(f"{stage}: owner 不匹配")
        artifact = record.get("artifact")
        if not isinstance(artifact, str) or not artifact:
            failures.append(f"{stage}: 缺少产物路径")
            continue
        path = (project / artifact).resolve()
        if not path.is_relative_to(project) or not path.is_file():
            failures.append(f"{stage}: 产物不存在或不在项目内")
            continue
        if file_digest(path) != record.get("artifact_sha256"):
            failures.append(f"{stage}: 产物在完成后发生变化")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化、读取或原子更新数学建模工作流状态")
    parser.add_argument("project_root", type=Path)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("init", help="缺失时创建状态文件；已存在时不覆盖")
    subparsers.add_parser("show", help="显示当前状态")
    audit_parser = subparsers.add_parser("audit", help="核对阶段责任、产物存在性和完成时哈希")
    audit_parser.add_argument("--require-through", choices=STAGES, help="要求截至该阶段全部完成")
    set_parser = subparsers.add_parser("set", help="设置一个阶段的状态")
    set_parser.add_argument("stage", choices=STAGES)
    set_parser.add_argument("status", choices=STATUSES)
    set_parser.add_argument("--actor", required=True, choices=tuple(STAGE_OWNERS.values()))
    set_parser.add_argument("--artifact", default="")
    set_parser.add_argument("--note", default="")
    args = parser.parse_args()

    project = args.project_root.resolve()
    if not project.is_dir():
        parser.error(f"项目目录不存在：{project}")
    path = state_path(project)
    if args.action == "init":
        if not path.exists():
            atomic_write(path, initial_state())
    elif args.action == "set":
        if args.actor != STAGE_OWNERS[args.stage]:
            parser.error(f"阶段 {args.stage} 只能由 {STAGE_OWNERS[args.stage]} 更新")
        artifact = args.artifact
        artifact_sha256 = ""
        if args.status == "complete":
            if not artifact:
                parser.error("阶段标记为 complete 时必须提供 --artifact")
            data = load(path)
            missing = [stage for stage in STAGES[: STAGES.index(args.stage)] if data["stages"][stage] != "complete"]
            if missing:
                parser.error(f"上游阶段尚未完成：{', '.join(missing)}")
            candidate = Path(artifact)
            candidate = candidate.resolve() if candidate.is_absolute() else (project / candidate).resolve()
            if not candidate.is_relative_to(project) or not candidate.is_file():
                parser.error("完成阶段的产物必须是真实文件且位于项目目录内")
            artifact = candidate.relative_to(project).as_posix()
            artifact_sha256 = file_digest(candidate)
        atomic_write(
            path,
            update_state(load(path), args.stage, args.status, artifact, artifact_sha256, args.note, args.actor),
        )
    elif args.action == "audit":
        if not path.is_file():
            print(json.dumps({"status": "FAIL", "failures": ["工作流状态文件不存在"]}, ensure_ascii=False, indent=2))
            return 1
        data = load(path)
        failures = audit_state(data, project, args.require_through)
        print(json.dumps({"status": "PASS" if not failures else "FAIL", "failures": failures}, ensure_ascii=False, indent=2))
        return 0 if not failures else 1
    print(json.dumps(load(path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
