# 阶段责任与模型参数冻结

完整竞赛工作流使用单一证据链。每个阶段只能修改自己拥有的产物；发现上游问题时提交变更请求并退回责任阶段，不能在下游悄悄改口径。

## 责任矩阵

| 阶段 / Skill | 可修改 | 只读输入 | 禁止行为 |
| --- | --- | --- | --- |
| `1start-mathmodel` | `plan.md`、`todo.md`、输入清单、工作流状态 | 用户文件和已有产物 | 选模型、改结果、写论文结论 |
| `2analysis-modeling` | `TASK_CONTRACT.md`、`RAG_CONTEXT.md`、`ANALYSIS_MODELING_REPORT.md`、`MODEL_FREEZE.json` | 题面、附件、输入清单 | 伪造计算结果或提前写论文 |
| `3coding-visual` | `code/`、`results/`、数据图、`RESULTS_REPORT.md`、结果证书、代码阶段变更请求 | 全部冻结的建模产物 | 修改题意、模型目标、约束、参数冻结或论文正文 |
| `4drawio` | 非数据图源文件/PDF、`DRAWIO_REPORT.md` | 冻结模型、真实结果、图表登记 | 重跑模型、改变数据图或数值结论 |
| `5writing` | `paper/` | 冻结模型、结果、证书、图表 | 改模型、重算结果、制造缺失数字或在上游报告中“协调”冲突 |
| `6verity` | `VERIFY_REPORT.md` 和验收日志 | 全部项目产物 | 代替责任阶段修模型、改数据或改论文论证；发现问题必须判定失败并退回 |

直接修复仅限责任阶段自己的文件。跨阶段问题写入 `reports/CHANGE_REQUESTS.md`，至少记录发现者、受影响问题、当前证据、建议返回阶段和是否会改变摘要结论。模型目标、数据口径、硬约束、评价指标或结论边界发生变化时，必须回到 `2analysis-modeling`。

## 冻结文件

分析阶段在开始正式编码前创建并封印：

```text
reports/TASK_CONTRACT.md
reports/ANALYSIS_MODELING_REPORT.md
reports/MODEL_FREEZE.json
```

`MODEL_FREEZE.json` 必须固定：

- 题目标识、顶层问题及顺序；
- 数据范围、样本/分组单位、缺失处理、随机种子和数值容差；
- 每问的目标、模型族、输入、输出和硬约束；
- 固定参数，或只使用训练数据决定参数的明确选择规则；
- 求解器、关键设置、停止条件与失败策略；
- 基线、划分方法、指标、敏感性方案和可验收阈值；
- `TASK_CONTRACT.md`、建模报告与输入清单的 SHA-256。

初始化草稿：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> init \
  --problem-id contest-year-problem --title "赛题标题" \
  --question Q1 --question Q2
```

填写所有字段后由分析阶段封印：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> seal
python <插件根目录>/scripts/model_freeze.py <项目根目录> check
```

空字段、占位符、缺少参数/选择规则、无验证阈值、源文件缺失或源文件在封印后改变，都会使检查失败。

## 下游接受回执

每个下游阶段开始前先检查并接受当前冻结版本：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> accept --role 3coding-visual
python <插件根目录>/scripts/model_freeze.py <项目根目录> accept --role 4drawio
python <插件根目录>/scripts/model_freeze.py <项目根目录> accept --role 5writing
```

回执写入 `reports/model-freeze-receipts/<role>.json`。验收阶段可一次检查关键回执：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> check \
  --receipt-role 3coding-visual --receipt-role 5writing
```

结果证书必须记录同一个 `model_freeze_sha256` 和 `model_freeze_revision`。冻结内容或上游报告被修改后，旧回执和结果证书自动失效。

## 变更控制

代码阶段只能进行不改变数学含义的等价实现，例如函数拆分、向量化、缓存或数值稳定化。出现下列任一情况必须停止正式计算并提交变更请求：

- 需要新增、删除或改变决策变量、模型族、目标函数或硬约束；
- 需要改变数据样本范围、分组单位、标签、特征可用时点或缺失处理；
- 需要补设冻结文件没有明确给出的参数、搜索空间、停止条件或评价指标；
- 当前模型不可行、不可识别、数值不稳定，且修复会改变数学定义；
- 结果与题意冲突，无法用实现错误解释。

只有 `2analysis-modeling` 可以打开新修订版：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> revise \
  --reason "说明证据、影响和变更原因"
```

分析阶段更新任务契约、建模报告和冻结草稿后重新执行 `seal`。所有受影响的下游阶段重新接受并运行；不得复用旧版本结果冒充新模型证据。
