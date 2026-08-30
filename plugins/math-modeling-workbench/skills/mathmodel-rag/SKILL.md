---
name: mathmodel-rag
description: Use the bundled Chinese mathematical-modeling RAG when solving, reviewing, or writing competition models. It covers CUMCM 2000-2025 A/B/C plus 21 curated Shenzhen Cup, MathorCup, Electrical Engineering Cup, May Day, and China Postgraduate/Huawei Cup problems, retrieving transferable decomposition, assumptions, algorithms, metrics, sensitivity, writing patterns, and source-audit rules.
---

# Mathematical Modeling RAG

Use this skill before proposing a model for a new mathematical-modeling problem. Retrieval supplies analogies and checklists, not an official answer.

## Workflow

1. Decompose every subquestion into object, data, unknowns, objective, hard/soft constraints, dependencies, and required outputs.
2. Build a Chinese query containing the background, task, data form, goal, and constraints. Do not query only by contest title.
3. Run:

   ```powershell
   python scripts/retrieve_modeling_kb.py "<structured problem description>" --top-k 12 --format prompt
   ```

   Resolve the script relative to this skill directory. If the command is launched elsewhere, pass its absolute path.
4. Use at least one relevant historical subquestion or problem overview, one algorithm card, and one strategy card when available. Prefer mathematical-structure similarity over title similarity, and state what transfers and what differs.
5. Establish an executable, interpretable baseline first. Upgrade only for a demonstrated residual, constraint, accuracy, or robustness gap.
6. Provide definitions, equations, solver, complexity, evaluation, sensitivity/robustness, failure cases, and reproducibility notes for each subquestion.
7. Read `source_grade`, `assumptions`, `sensitivity`, and `writing_pattern` from retrieved chunks. Treat B-grade material only as a candidate method, not as evidence for a conclusion.
8. For a competition-specific or current topic, browse authoritative sources when available. Label sources as official problem/review, verified award paper, ordinary paper, or informal article; never infer "award paper" from the topic alone.

## Mandatory guards

- Do not mechanically copy an algorithm because a title is similar.
- Do not invent attachment data, numerical results, citations, or prize provenance.
- Keep fitting/tuning separate from final evaluation and report distributional or worst-case metrics when relevant.
- Check feasibility and bounds before interpreting an optimizer's objective value.
- Do not call a method an "official answer" merely because it appears in a public paper. Mathematical-modeling contests usually have no unique canonical solution.
- Propagate uncertainty between dependent subquestions; do not pass a point prediction into an optimizer as if it were exact.
- For color-display problems, explicitly audit transfer functions, white point/white balance, drive bounds, perceptual color difference, common reachable gamut, and LUT deployment.

The packaged corpus and index are under `references/kb/`. Read `references/kb/README.md` for deployment details and `references/kb/CROSS_CONTEST_SELECTION.md` for quality scores, selected cases, exclusions, and source policy when provenance matters.
