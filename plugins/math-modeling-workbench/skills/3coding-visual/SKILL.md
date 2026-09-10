---
name: 3coding-visual
description: "数学建模编程实现与数据图表生成阶段。根据 ANALYSIS_MODELING_REPORT.md 编写可复现代码、运行求解、验证约束、输出 RESULTS_REPORT.md 并生成论文可用的数据驱动图表 PDF。"
---

# 编程实现与数据图表生成

本 skill 承接 `2analysis-modeling`。目标是把 `reports/ANALYSIS_MODELING_REPORT.md` 里的模型和算法落实为可复现程序，跑出可信结果，并生成论文中需要的数据型图表。

## 数学建模规范参考

如需领域判断，读取 `../mathmodel-reference/math_modeling_norms.md` 中的“题型防错速查”“代码实现与结果”“编码阶段常见错误”和“图表与可视化”小节。该文件只作为规范知识库，不新增本阶段的固定产物。

开始前读取 `../mathmodel-reference/roles-and-freeze.md`。本阶段拥有实现与计算产物，但对题意、模型、参数冻结和论文均为只读。

## 阶段边界

- 本阶段负责：代码、实验运行、结果、结果表、数据驱动图表。
- 本阶段不负责：技术路线图、算法流程图、系统架构图、概念示意图。这些交给 `4drawio`。
- 本阶段不写论文正文，只为 `5writing` 提供可信数值和图表资产。

## 模型冻结门禁

正式编码前必须执行：

```bash
python <插件根目录>/scripts/model_freeze.py <项目根目录> check
python <插件根目录>/scripts/model_freeze.py <项目根目录> accept --role 3coding-visual
```

检查失败时停止。若实现需要改变题意、数据范围、模型族、目标、硬约束、参数、搜索空间、停止条件或评价指标，只能把证据与影响追加到 `reports/CHANGE_REQUESTS.md`，再退回 `2analysis-modeling` 执行 `revise`；不得直接修改三个冻结上游文件。

## 附件与大文件预检

开始编码前读取 `reports/INPUT_INVENTORY.md`。若文件不存在，先运行插件根目录的 `scripts/inspect_project_inputs.py`，再根据清单确认文件编码、工作表、字段、单位和数据规模。

- 对达到清单大文件阈值的数据使用分块读取、列裁剪、类型下推或数据库聚合；不得为了预览一次性载入全部数据。
- 抽样只用于结构理解和快速诊断。最终统计、训练、约束验证与结果证书必须明确说明使用的是全量数据还是经过设计的抽样数据。
- XLSX 先按工作表分别核对表头和数据范围，不执行宏，不把公式缓存值误认为已经重新计算的结果。
- 读取失败时记录编码、解析器和失败文件，不得跳过附件后继续编造字段。


### Step 1: 代码结构

按 `plan.md` 中"项目目录结构"创建 `code/` 和 `figures/` 骨架，再开始写代码。子问题数不一定是 3，按赛题实际数量调整。


### Step 2: 逐子问题实现

按子问题顺序实现，不要一次性写完不跑。

每个子问题必须完成：

1. 读取所需数据。
2. 实现模型或算法。
3. 验证约束。
4. 输出核心结果。
5. 绘制丰富的图表。
6. 在 `reports/RESULTS_REPORT.md` 中写清楚方法、关键数值和校验结果。

每个耗时步骤应把已完成的预处理、参数、随机种子和中间结果写入 `code/outputs/`。恢复运行时先验证这些检查点与当前输入文件一致，再决定复用或重算。

最终运行后必须按 `references/result-certificate-schema.md` 生成 `code/outputs/validation_certificate.json`，记录当前冻结版本和哈希，并运行：

```bash
python <插件根目录>/scripts/validate_result_certificate.py \
  code/outputs/validation_certificate.json --freeze reports/MODEL_FREEZE.json
```

证书未通过时，不得把目标值写成“最优结果”或把外部结果差异写成“误差”；应先修复实现错误，或按变更控制退回分析阶段。

优化类问题必须先保证可行解，再优化目标值。预测类问题必须做训练/验证划分或合理误差评估。评价类问题必须说明指标方向、归一化方法和权重来源。

若存在公开论文、排行榜或参考实现，必须从其导出的决策/预测文件独立复算核心指标。比较前核对单位、时间范围、数据版本、目标口径和硬约束；任一不一致就标记为不可比，不输出伪精确的相对误差。

### Step 3: 结果文件格式


AI 在实现、求解和作图过程中，必须把关键中间过程保存成数据并做好记录，例如清洗后的数据摘要、模型参数、迭代历史、约束检查、灵敏度分析过程、图表所用数据和运行日志。中间数据优先保存到 `figures/` 或 `code/outputs/`，并在 `reports/RESULTS_REPORT.md` 中说明文件用途。

`reports/RESULTS_REPORT.md` 推荐结构：

```markdown
# 计算结果

## 运行环境
## 数据读取与预处理
## 问题一结果
## 问题二结果
## 问题三结果
## 灵敏度分析
## 约束与一致性校验
## 与建模报告的一致性说明
## 可复现运行方式
```

所有数据和图表结果都必须出现在 `reports/RESULTS_REPORT.md` 中引用

### Step 4: 生成数据驱动图表

根据 `reports/ANALYSIS_MODELING_REPORT.md` 和 `reports/RESULTS_REPORT.md` 规划图表，生成 PDF 到 `figures/`。

典型图表：

- 预测类：真实值-预测值对比、误差分布、指标对比。
- 优化类：收敛曲线、成本对比、资源利用率、方案前后对比。
- 评价类：综合得分排序、雷达图、热力图、敏感性曲线。
- 数据理解：分布图、趋势图、相关性图、箱线图。

图表要求：

- PDF 矢量输出，适合论文。
- 不在图内写大标题，标题交给论文 caption（Typst 的 `caption:` 或 LaTeX 的 `\caption{}`）。
- 中文论文图表使用中文坐标轴和图例；英文论文使用英文。
- 不生成流程图/架构图/路线图。

图表可以由主程序或独立脚本生成，不强制固定脚本名。无论采用哪种方式，都必须保存图表对应的数据来源和生成记录。

完成后以 `RESULTS_REPORT.md` 为阶段产物更新状态：

```bash
python <插件根目录>/scripts/manage_workflow_state.py <项目根目录> set coding complete \
  --actor 3coding-visual --artifact reports/RESULTS_REPORT.md
```
