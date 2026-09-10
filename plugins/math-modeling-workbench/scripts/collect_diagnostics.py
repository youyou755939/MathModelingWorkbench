#!/usr/bin/env python3
"""Collect a redacted, local-only diagnostic report for the workbench."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


COMMANDS = ("python", "python3", "typst", "xelatex", "drawio", "pdftoppm", "mutool", "magick")
PACKAGES = ("numpy", "scipy", "pandas", "matplotlib", "scikit-learn", "openpyxl", "pypdf")


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "未安装"


def plugin_version(root: Path) -> str:
    try:
        data = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(data.get("version", "未知"))
    except (OSError, ValueError, TypeError):
        return "未知"


def project_summary(project: Path | None) -> list[str]:
    if project is None:
        return ["- 未指定项目目录。"]
    expected = (
        "plan.md", "todo.md", "reports/INPUT_INVENTORY.md", "reports/WORKFLOW_STATE.json",
        "reports/TASK_CONTRACT.md", "reports/ANALYSIS_MODELING_REPORT.md", "reports/MODEL_FREEZE.json",
        "reports/RESULTS_REPORT.md", "reports/VERIFY_REPORT.md",
        "code", "figures", "paper", "results",
    )
    lines = [f"- 项目名：`{project.name}`"]
    for relative in expected:
        lines.append(f"- `{relative}`：{'存在' if (project / relative).exists() else '缺失'}")
    return lines


def render(root: Path, project: Path | None) -> str:
    lines = [
        "# 数学建模工作台本地诊断",
        "",
        f"生成时间：{datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"插件版本：`{plugin_version(root)}`",
        f"操作系统：`{platform.platform()}`",
        f"Python：`{sys.version.split()[0]}`",
        "",
        "> 本报告不会读取环境变量值、API Key、题目正文或附件内容，也不会自动上传。",
        "",
        "## 命令可用性",
        "",
        "| 命令 | 状态 |",
        "| --- | --- |",
    ]
    for command in COMMANDS:
        location = shutil.which(command)
        lines.append(f"| `{command}` | {'可用' if location else '缺失'} |")
    lines.extend(["", "## Python 包", "", "| 包 | 版本 |", "| --- | --- |"])
    for package in PACKAGES:
        lines.append(f"| `{package}` | `{package_version(package)}` |")
    lines.extend(["", "## 插件完整性", ""])
    checks = {
        "插件清单": root / ".codex-plugin" / "plugin.json",
        "工作流入口": root / "skills" / "1start-mathmodel" / "SKILL.md",
        "参数冻结器": root / "scripts" / "model_freeze.py",
        "稀疏检索器": root / "skills" / "mathmodel-rag" / "scripts" / "retrieve_modeling_kb.py",
        "论文模板": root / "skills" / "5writing" / "templates",
        "验收脚本": root / "skills" / "6verity" / "scripts" / "writing_check.sh",
    }
    for label, path in checks.items():
        lines.append(f"- {label}：{'存在' if path.exists() else '缺失'}")
    lines.extend(["", "## 项目状态", ""])
    lines.extend(project_summary(project))
    lines.extend([
        "",
        "## 分享前检查",
        "",
        "- 报告默认不含绝对路径和密钥值，但分享前仍应人工检查项目名是否敏感。",
        "- 如需他人排查，只发送本报告和明确报错；不要发送 `.env`、密钥文件或完整私有数据。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成不上传、不读取密钥值的本地诊断报告")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.plugin_root.resolve()
    project = args.project_root.resolve() if args.project_root else None
    output = args.out.resolve() if args.out else (project / "reports" / "DIAGNOSTICS.md" if project else None)
    report = render(root, project)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(json.dumps({"output": str(output)}, ensure_ascii=False))
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
