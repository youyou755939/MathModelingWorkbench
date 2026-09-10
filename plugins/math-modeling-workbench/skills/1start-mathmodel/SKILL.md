---
name: 1start-mathmodel
description: "数学建模竞赛工作流入口。用于检查题面与附件、恢复已有进度、记录用户偏好，生成计划和状态文件，并按阶段调用分析、建模、代码、图表、论文与验收 skills。"
---

# 数学建模工作流

本 skill 是数学建模竞赛项目的总控入口。它不替代后续阶段 skill，而是负责附件预检、断点恢复、询问偏好、记录决策、生成计划，并按顺序调用各阶段 skill。

## 数学建模规范参考

如需领域判断，读取 `../mathmodel-reference/math_modeling_norms.md`。该文件只提供数学建模基本规范和防错知识，不改变本 skill 的阶段顺序和产出约定。

完整流程还必须读取 `../mathmodel-reference/roles-and-freeze.md`。总控只管理输入、计划、状态和阶段切换，不替下游角色修改其专属产物。

## 必须产出

在当前工作目录中创建或更新以下文件：

- `plan.md`：整体流程方案、建模方向、阶段顺序、预期产物和风险控制。
- `todo.md`：具体待办事项列表，记录每个阶段的任务和状态。
- `reports/INPUT_INVENTORY.md`：题面和数据附件的本地清单、有界预览及大文件标记。
- `reports/WORKFLOW_STATE.json`：机器可读的阶段状态和恢复点。

## 工作流

### 0. 检查输入与恢复点

开始前运行插件根目录的附件预检脚本：

```bash
python <插件根目录>/scripts/inspect_project_inputs.py <项目根目录>
```

脚本只在本地读取附件，不执行 Office 宏、不上传数据；它对 CSV/TSV/XLSX 做有界结构预览，对大文件只抽样探查。读取 `reports/INPUT_INVENTORY.md` 后，先确认题面、附件、工作表和关键字段是否齐全，再进入建模。

若 `plan.md`、`todo.md` 或 `reports/WORKFLOW_STATE.json` 已存在，不要重新初始化并覆盖。读取 `references/project-state.md`，核对真实产物，找到第一个未完成阶段继续。状态文件与真实产物冲突时，以经过检查的真实产物为准。

使用状态脚本初始化或更新恢复点；脚本采用原子写入，不会覆盖已经存在的状态文件：

```bash
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> init
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> set intake complete \
  --actor 1start-mathmodel --artifact reports/INPUT_INVENTORY.md
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> show
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> audit
```

若项目根存在 `project-profile.json`，读取其中的比赛、语言、排版和队伍资料作为候选默认值；必须让本次用户选择和当届官方规则覆盖旧值。不得在该文件保存密钥或身份凭证。

### 1. 询问用户偏好

在规划前，只询问会实质影响流程的问题。问题要少而关键。

优先询问（按重要性排序）：

1. **排版引擎**：Typst 还是 LaTeX？— 决定 5writing 使用哪套模板和编译命令。两套引擎均覆盖全部模板（14 中 + 3 英）。Typst 使用 `typst` 命令编译；LaTeX 使用 `xelatex` 命令编译（需跑两遍解决交叉引用）。
2. **竞赛类型**：国赛/华为杯/华中杯/MCM/...— 决定模板选择，见 5writing 的模板族清单。
3. **论文语言**：中文/英文 — MCM/ICM/COMAP 强制英文，其他默认中文。
4. **子问题数量是否已知**：影响章节文件生成数量。若未知，由 2analysis-modeling 阶段根据题面确定。

将用户的选择记录到 `plan.md` 的"方案"小节中。

用户明确提供队伍或比赛信息且希望复用时，按 `references/project-state.md` 创建或更新 `project-profile.json`。未得到资料时保留空字段，不得猜测。


### 2. 制定方案

按以下结构编写 `plan.md`：

```markdown
# 方案

要依次调用这些 skill，按照里面要求完成任务。

用户偏好：
- 排版引擎：<Typst / LaTeX>
- 竞赛类型：<国赛 / 华为杯 / MCM / ...>
- 论文语言：<中文 / 英文>
- 子问题数量：<已知 N 个 / 待分析确定>

workflow:
   step      skills
1. 赛题分析、RAG 检索、建模设计与参数冻结 - `2analysis-modeling` + `mathmodel-rag`
2. 编程实现和图表生成 - `3coding-visual`
3. 流程与架构图绘制 - `4drawio`
4. 竞赛论文撰写 - `5writing`
5. 验证和验收 - `6verity`
```

## 项目目录结构

各阶段按此骨架创建和填充文件：

```text
.
├── plan.md                      # 1: 本文件
├── todo.md                      # 1: 待办事项
├── project-profile.json         # 1: 可选、用户控制的可复用参赛资料
├── reports/                     # 各阶段文档报告
│   ├── INPUT_INVENTORY.md           # 0: 输入附件清单与有界预览
│   ├── WORKFLOW_STATE.json           # 0-5: 阶段状态与恢复点
│   ├── TASK_CONTRACT.md               # 1: 题意、数据口径和逐问输出契约
│   ├── ANALYSIS_MODELING_REPORT.md  # 1: 赛题分析-建模报告（2analysis-modeling）
│   ├── RAG_CONTEXT.md               # 1: 历史题、算法卡、策略卡及迁移差异
│   ├── MODEL_FREEZE.json              # 1: 带哈希封印的模型与参数契约
│   ├── model-freeze-receipts/         # 2-5: 下游角色接受冻结版本的回执
│   ├── CHANGE_REQUESTS.md             # 2-5: 跨阶段变更请求（仅在需要时）
│   ├── RESULTS_REPORT.md            # 2: 结果报告（3coding-visual）
│   ├── DRAWIO_REPORT.md             # 3: 非数据图说明（4drawio）
│   ├── VERIFY_REPORT.md             # 5: 验收报告（6verity）
├── code/                        # 2: 代码（3coding-visual）
│   ├── problem1.py
│   ├── problem2.py
│   ├── problem3.py               # 问题的数量应该更具题目动态调整
│   ├── ... 
│   └── utils.py
├── results/                     # 2: 结果记录（3coding-visual）
├── figures/                     # 2+3: 所有图表（3coding-visual + 4drawio）
│   ├── *.pdf                    #     数据图 + 非数据图 PDF
│   ├── *.drawio                 #     非数据图源文件
├── paper/                       # 4: 论文（5writing）
│   ├── main.typ / main.tex      #     论文主文件（按用户选择的引擎）
│   └── sections/                #     各节文件（.typ 或 .tex）
```

方案必须明确每个阶段由哪个下游 skill 负责，以及该阶段应产出什么文件。

### 3. 生成待办

将 `todo.md` 写成阶段性 checklist，格式如下：

```markdown
# 待办事项

- [ ] 1. 赛题分析、RAG 检索、建模设计与参数冻结 - `2analysis-modeling` + `mathmodel-rag`
- [ ] 2. 编程实现和图表生成 - `3coding-visual`
- [ ] 3. 流程与架构图绘制 - `4drawio`
- [ ] 4. 竞赛论文撰写 - `5writing`
- [ ] 5. 验证和验收 - `6verity`
```

每完成一个阶段，都要更新 `todo.md` 中对应任务的状态。
同时更新 `reports/WORKFLOW_STATE.json`；只有产物存在且通过该阶段轻量检查后才能标记为 `complete`。
优先调用插件根目录的 `scripts/manage_workflow_state.py` 更新，避免中断时写出半截 JSON。

### 4. 依次执行阶段

按以下顺序调用下游 skills：

| 阶段 | Skill | 作用 | 主要产物 |
| --- | --- | --- | --- |
| 赛题分析与建模设计 | `2analysis-modeling` + `mathmodel-rag` | 统一题意和数据口径，选择模型并冻结参数、求解和验证规则。 | `TASK_CONTRACT.md`, `RAG_CONTEXT.md`, `ANALYSIS_MODELING_REPORT.md`, `MODEL_FREEZE.json` |
| 编程实现和图表生成 | `3coding-visual` | 实现可复现代码，运行实验，生成结果表和多种多样的图表。 | `code/`, `results/` ,  `RESULTS_REPORT.md`, `figures/图表` |
| 流程与架构图绘制 | `4drawio` | 在论文确实需要时，绘制方法流程图、架构图和非数据型概念图。 | `figures/*.drawio`, `figures/*.pdf`, `DRAWIO_REPORT.md` |
| 竞赛论文撰写 | `5writing` | 基于分析、建模、代码结果和图表撰写最终竞赛论文，并按章节直接插入图表。 | `paper/` |
| 验证和验收 | `6verity` | 检查可复现性、一致性、产物完整性、格式规范和提交就绪状态。 | `VERIFY_REPORT.md` |

## 阶段边界

- 严格遵守 `../mathmodel-reference/roles-and-freeze.md` 的责任矩阵；总控不得为追求进度直接修改下游专属产物。
- `analysis` 只有在 `MODEL_FREEZE.json` 成功封印后才能完成；`coding`、`diagram`、`writing` 开始前必须生成对应冻结接受回执。
- 任何阶段完成时都用自己的 Skill 名作为 `manage_workflow_state.py set --actor`；冒用其他角色会被脚本拒绝。
- `3coding-visual` 负责生成所有依赖计算结果或实验输出的数据图表。
- `4drawio` 只负责概念图、算法流程图、架构图、路线图等非数据型图示。
- 不要让 `4drawio` 重复绘制 `3coding-visual` 已经生成的统计图或数据图。
- `5writing` 负责决定图表在论文中的位置，并按所选引擎写入图表代码：
  - Typst：`#figure(image("../../figures/xxx.pdf", width: 85%), caption: [...])`
  - LaTeX：`\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{../../figures/xxx.pdf}\caption{...}\label{fig:xxx}\end{figure}`
- 不要让 `5writing` 编造数值结论。论文中的数值必须来自 `RESULTS_REPORT.md`、结果表或已生成图表的数据。
- 命令失败、会话中断或用户暂停时，保留已验证产物并把当前阶段标记为 `failed` 或 `in_progress`，记录恢复说明；不要从头覆盖整个项目。
