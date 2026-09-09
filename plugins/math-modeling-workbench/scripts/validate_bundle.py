#!/usr/bin/env python3
"""Validate the self-contained Math Modeling Workbench plugin bundle."""

from __future__ import annotations

import gzip
import importlib.util
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED_SKILLS = {
    "1start-mathmodel",
    "2analysis-modeling",
    "3coding-visual",
    "4drawio",
    "5writing",
    "6verity",
    "doctor",
    "mathmodel-figure-templates",
    "mathmodel-rag",
    "mathmodel-reference",
    "typst-author",
}
FORBIDDEN_MARKERS = (
    "local " "developer",
    "/home/user/" ".claude",
    "[todo" ":",
)


class ValidationFailure(RuntimeError):
    """Raised when a plugin invariant is not satisfied."""


def require(condition: bool, message: str) -> None:
    """Raise a concise validation error when a condition is false."""
    if not condition:
        raise ValidationFailure(message)


def load_json(path: Path) -> dict:
    """Load a JSON object from disk."""
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def validate_manifest() -> None:
    """Validate plugin metadata and bundled skill declarations."""
    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path)
    name = manifest.get("name")
    version = manifest.get("version")
    source_layout = name == ROOT.name
    installed_cache_layout = name == ROOT.parent.name and version == ROOT.name
    require(source_layout or installed_cache_layout, "Plugin name must match its source or installed-cache folder")
    require(manifest.get("skills") == "./skills/", "Plugin must expose ./skills/")
    author = manifest.get("author", {})
    require(author.get("name") == "Math Modeling Workbench", "Publisher must be product-only")
    interface = manifest.get("interface", {})
    require(
        interface.get("developerName") == "Math Modeling Workbench",
        "Developer metadata must not identify a person",
    )
    prompts = interface.get("defaultPrompt")
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Need 1-3 starter prompts")
    require((ROOT / "assets" / "icon.png").is_file(), "Plugin icon is missing")


def read_frontmatter_name(path: Path) -> str:
    """Read the required name field from simple YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n") or text.startswith("---\r\n"), f"Missing frontmatter: {path}")
    match = re.search(r"(?m)^name:\s*[\"']?([^\"'\r\n]+)", text)
    require(match is not None, f"Missing skill name: {path}")
    return match.group(1).strip()


def validate_skills() -> None:
    """Validate required skill folders, names, references, and scripts."""
    present = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    require(REQUIRED_SKILLS <= present, f"Missing skills: {sorted(REQUIRED_SKILLS - present)}")
    for folder in sorted(REQUIRED_SKILLS):
        skill_file = SKILLS / folder / "SKILL.md"
        require(skill_file.is_file(), f"Missing SKILL.md: {folder}")
        require(read_frontmatter_name(skill_file) == folder, f"Skill name mismatch: {folder}")

    require(
        (SKILLS / "6verity" / "scripts" / "writing_check.sh").is_file(),
        "Writing acceptance script is missing",
    )
    require(
        (SKILLS / "mathmodel-reference" / "math_modeling_norms.md").is_file(),
        "Shared modeling reference is missing",
    )


def validate_templates() -> None:
    """Require Typst/LaTeX pairs and valid entry files for every template."""
    template_root = SKILLS / "5writing" / "templates"
    for language in ("zh", "en"):
        language_root = template_root / language
        require(language_root.is_dir(), f"Missing template language: {language}")
        names = {path.name for path in language_root.iterdir() if path.is_dir()}
        typst_names = {name for name in names if not name.endswith("-latex")}
        latex_names = {name.removesuffix("-latex") for name in names if name.endswith("-latex")}
        require(typst_names == latex_names, f"Unpaired {language} templates")
        for name in typst_names:
            require((language_root / name / "main.typ").is_file(), f"Missing main.typ: {language}/{name}")
            require(
                (language_root / f"{name}-latex" / "main.tex").is_file(),
                f"Missing main.tex: {language}/{name}-latex",
            )


def load_retriever(path: Path):
    """Load the bundled RAG implementation without installing dependencies."""
    spec = importlib.util.spec_from_file_location("_mathmodel_plugin_retriever", path)
    require(spec is not None and spec.loader is not None, "Cannot load RAG retriever")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_rag() -> None:
    """Validate corpus/index/store integrity and one diversified retrieval."""
    rag_root = SKILLS / "mathmodel-rag"
    kb = rag_root / "references" / "kb"
    manifest = load_json(kb / "manifest.json")
    chunks = []
    with (kb / "chunks.jsonl").open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValidationFailure(f"Invalid chunk JSON at line {line_number}") from exc
    require(len(chunks) == manifest["chunk_count"], "RAG chunk count differs from manifest")
    ids = [chunk["chunk_id"] for chunk in chunks]
    require(len(ids) == len(set(ids)), "RAG chunk_id values must be unique")
    kinds = Counter(chunk["chunk_type"] for chunk in chunks)
    require(dict(kinds) == manifest["chunk_types"], "RAG chunk type counts differ from manifest")

    with gzip.open(kb / "retrieval_index.json.gz", "rt", encoding="utf-8") as handle:
        index = json.load(handle)
    require(set(index["doc_len"]) == set(ids), "Sparse index doc_len is incomplete")
    require(set(index["doc_tf"]) == set(ids), "Sparse index doc_tf is incomplete")

    with sqlite3.connect(kb / "cumcm_rag.sqlite") as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    require(integrity == "ok", f"SQLite integrity check failed: {integrity}")

    retriever = load_retriever(rag_root / "scripts" / "retrieve_modeling_kb.py")
    query = "预测未来需求及区间，再在容量、轮作和风险约束下制定多年度资源配置方案"
    results, _, _ = retriever.retrieve(query, kb, 12)
    result_types = {item["chunk_type"] for item in results}
    require(
        {"algorithm_card", "strategy_card"} <= result_types
        and bool({"case_subquestion", "problem_overview"} & result_types),
        "RAG smoke query did not return case, algorithm, and strategy evidence",
    )


def validate_portability() -> None:
    """Reject known identity remnants and non-portable hard-coded paths."""
    text_suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".sh", ".toml", ".ts", ".tex", ".typ"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in FORBIDDEN_MARKERS:
            require(marker not in text, f"Forbidden marker {marker!r} in {path.relative_to(ROOT)}")


def main() -> int:
    """Run every bundle check and return a process exit code."""
    checks = (
        ("manifest", validate_manifest),
        ("skills", validate_skills),
        ("templates", validate_templates),
        ("rag", validate_rag),
        ("portability", validate_portability),
    )
    try:
        for label, check in checks:
            check()
            print(f"PASS {label}")
    except (OSError, KeyError, TypeError, ValidationFailure) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS bundle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
