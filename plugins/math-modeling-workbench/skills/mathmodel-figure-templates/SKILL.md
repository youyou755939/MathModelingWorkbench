---
name: mathmodel-figure-templates
description: Use this skill when the user asks to generate one of the bundled scientific visualization templates, including SHAP组合图、配对云雨图、交叉验证ROC、泰勒图、相关矩阵组合图、预测真实值边缘分布图、TPE调参3D曲面、半边小提琴图、分组环形热图、城市公园降温组合图或和弦图. It provides ready-to-run Python scripts and reproducible multi-format output.
---

# Scientific Figure Templates

This skill is bundled in the current Codex plugin. Resolve every script relative to this `SKILL.md`; never assume a fixed home or sandbox path.

## Fast Path

1. Match the requested chart in `references/figure-catalog.md`.
2. From the user's current workspace, run the renderer with the template id:

```bash
python3 <skill-dir>/scripts/render_template.py paired-raincloud
```

3. The renderer copies the bundled template script into `科研绘图/scripts/`, runs it there, and writes outputs to `科研绘图/outputs/`.
4. Return the generated PNG/PDF/SVG paths and the copied script path to the user.

Use `--list` to show supported ids:

```bash
python3 <skill-dir>/scripts/render_template.py --list
```

## Output Contract

- Work under the current workspace unless the user gives another path.
- Default project folder: `科研绘图`.
- Script path: `科研绘图/scripts/make_<template>.py`.
- Outputs: `科研绘图/outputs/<template>.png`, `.pdf`, `.svg`.
- Use the bundled scripts as the first choice; edit the copied workspace script only when the user requests customization.
- The bundled scripts use deterministic simulated data. Do not claim simulated values reproduce a source study exactly.

## Template Ids

- `multiclass-shap-combo`
- `paired-raincloud`
- `cv-roc-ci`
- `taylor-diagram`
- `correlation-pairgrid`
- `prediction-marginal-grid`
- `rf-tpe-surface`
- `grouped-corr-split-violin`
- `grouped-circular-heatmap`
- `urban-park-cooling-combo`
- `nature-chord-diagram`

## When Customizing

If the user asks for changes, copy/run the nearest template first, then edit the copied file in `科研绘图/scripts/`. Preserve:

- `MPLCONFIGDIR` before importing matplotlib.
- deterministic seeds for simulated data.
- PNG/PDF/SVG export.
- readable labels, legends, and high-DPI output.

Use `references/plot-recipes.md` for implementation patterns.
