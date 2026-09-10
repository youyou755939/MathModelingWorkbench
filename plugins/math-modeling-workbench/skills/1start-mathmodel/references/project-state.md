# 项目状态与复用资料

## `project-profile.json`

这是用户可选、可复制到新项目的参赛资料文件。只记录用户明确提供且允许写入论文的信息，不保存 API Key、账号令牌或身份证件信息。

```json
{
  "schema_version": 1,
  "competition": "CUMCM",
  "paper_language": "zh",
  "typesetting_engine": "latex",
  "team": {
    "team_id": "",
    "school": "",
    "members": []
  }
}
```

字段可以为空。读取后仍须以本届官方规则和用户本次明确选择为准，不得把旧比赛信息静默带入新论文。

## `reports/WORKFLOW_STATE.json`

该文件用于断点恢复，不是论文素材。每完成一个阶段就原子性地更新状态；不要只更新 `todo.md` 而遗漏机器可读状态。

```json
{
  "schema_version": 1,
  "updated_at": "ISO-8601 timestamp",
  "active_stage": "analysis",
  "stages": {
    "intake": "complete",
    "analysis": "in_progress",
    "coding": "pending",
    "diagram": "pending",
    "writing": "pending",
    "verification": "pending"
  },
  "stage_records": {
    "intake": {
      "owner": "1start-mathmodel",
      "artifact": "reports/INPUT_INVENTORY.md",
      "artifact_sha256": "64-character SHA-256",
      "completed_at": "ISO-8601 timestamp"
    }
  },
  "last_verified_artifact": "reports/INPUT_INVENTORY.md",
  "recovery_note": ""
}
```

允许状态：`pending`、`in_progress`、`complete`、`failed`。恢复时必须同时检查状态文件和真实产物；若两者冲突，以真实文件及其可验证内容为准，并在 `recovery_note` 记录修正。

## 恢复规则

1. 不覆盖已存在且非空的可信产物。
2. 找到第一个未完成或验证失败的阶段，从该阶段继续。
3. 上游文件被修改后，所有依赖它的下游阶段重新标为 `pending`。
4. 命令中断时保留日志和部分产物，但不得将部分结果标记为 `complete`。
5. 恢复后先运行轻量一致性检查，再决定是否重跑耗时计算。

## 阶段责任与产物哈希

阶段完成必须提供与阶段匹配的 `--actor` 和一个真实文件产物。状态脚本记录产物 SHA-256；上游产物变化会使下游阶段重新变为 `pending`。

| 阶段 | actor | 建议完成产物 |
| --- | --- | --- |
| intake | `1start-mathmodel` | `reports/INPUT_INVENTORY.md` |
| analysis | `2analysis-modeling` | `reports/MODEL_FREEZE.json` |
| coding | `3coding-visual` | `reports/RESULTS_REPORT.md` |
| diagram | `4drawio` | `reports/DRAWIO_REPORT.md` |
| writing | `5writing` | `paper/main.typ` 或 `paper/main.tex` |
| verification | `6verity` | `reports/VERIFY_REPORT.md` |

恢复与验收前运行：

```bash
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> audit
```

缺少完成记录、owner 不匹配、产物被修改或产物消失时，审计返回失败。不要手工把状态改成 `complete` 绕过门禁。
