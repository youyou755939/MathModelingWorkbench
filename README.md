<p align="center">
  <img src="plugins/math-modeling-workbench/assets/icon.png" width="116" alt="Math Modeling Workbench logo">
</p>

<h1 align="center">Math Modeling Workbench</h1>

<p align="center">
  <strong>数学建模工作台</strong><br>
  让 Codex 先把答案做对，再把论文做漂亮。
</p>

<p align="center">
  <img alt="Version 0.2.0" src="https://img.shields.io/badge/version-0.2.0-6287CC?style=for-the-badge">
  <img alt="Codex Plugin" src="https://img.shields.io/badge/Codex-Plugin-111827?style=for-the-badge&logo=openai&logoColor=white">
  <img alt="RAG 477 chunks" src="https://img.shields.io/badge/RAG-477%20chunks-185A7D?style=for-the-badge">
  <img alt="17 Typst and LaTeX template families" src="https://img.shields.io/badge/Templates-17%20%C3%97%202-7C3AED?style=for-the-badge">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-16A34A?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#六阶段工作流">工作流</a> ·
  <a href="#数学建模-rag">RAG</a> ·
  <a href="#论文与科研图表">论文与图表</a> ·
  <a href="#验证">验证</a>
</p>

---

> Math Modeling Workbench 不是“一次生成整篇论文”的提示词集合，而是一条可追踪的竞赛建模流水线：拆题、检索、选模、求解、制图、写作和验收都有明确产物与质量门禁。

## 为什么使用它

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🎯 先保证答案可信</h3>
      <p>按数学结构检索历史题与算法卡，先建立可解释基线，再比较候选模型；对硬约束、量纲、数据泄漏、灵敏度和可复现性进行显式检查。</p>
    </td>
    <td width="50%" valign="top">
      <h3>🎨 再提升论文表现</h3>
      <p>提供 Typst / LaTeX 双引擎模板、科研绘图脚本和 DrawIO 图示流程，让图表、公式、章节和视觉风格共同服务论文论证。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🧠 离线建模 RAG</h3>
      <p>覆盖 CUMCM 2000–2025 A/B/C 题及五类跨赛精选案例。检索只提供结构类比和检查清单，不把历史解法冒充当前题目的标准答案。</p>
    </td>
    <td width="50%" valign="top">
      <h3>✅ 提交前硬门禁</h3>
      <p>检查章节、图表、引用、关键数值、结果证书、编译和 PDF 视觉质量；发现硬错误时回退修复，而不是用润色掩盖问题。</p>
    </td>
  </tr>
</table>

## 六阶段工作流

```mermaid
flowchart LR
    A[题面与附件] --> B[拆题与 RAG]
    B --> C[模型设计]
    C --> D[代码求解与数据图]
    D --> E[流程图与架构图]
    E --> F[Typst / LaTeX 论文]
    F --> G[验证与提交验收]
    G -. 发现硬错误 .-> C
```

| 阶段 | Skill | 关键产物 |
| --- | --- | --- |
| 1. 启动与规划 | `1start-mathmodel` | `plan.md`、`todo.md` |
| 2. 分析与选模 | `2analysis-modeling` + `mathmodel-rag` | `ANALYSIS_MODELING_REPORT.md`、`RAG_CONTEXT.md` |
| 3. 求解与数据图 | `3coding-visual` | 可复现代码、结果证书、数据图、`RESULTS_REPORT.md` |
| 4. 非数据图示 | `4drawio` | 技术路线图、模型结构图、可编辑 DrawIO 源文件 |
| 5. 论文写作 | `5writing` | Typst / LaTeX 论文工程和 PDF |
| 6. 最终验收 | `6verity` | `VERIFY_REPORT.md` 与 PASS / FAIL 结论 |

## 数学建模 RAG

RAG 默认离线运行，不需要 API Key 或外部向量数据库。它使用中文字符 2/3-gram BM25、查询扩展、字段加权和知识类型配额，在一次检索中组合案例、算法和验证策略。

| 内容 | 数量 |
| --- | ---: |
| 历史子问题知识块 | 333 |
| 整题任务链与结构画像 | 99 |
| 算法知识卡 | 25 |
| 建模与验证策略卡 | 20 |
| **知识块合计** | **477** |

覆盖范围包括：

- CUMCM 2000–2025 A/B/C；
- 深圳杯、MathorCup、电工杯、五一数学建模竞赛；
- 中国研究生数学建模竞赛（华为杯）精选题；
- 预测、评价、优化、图论、统计、机器学习、机理模型和稳健性分析等通用范式。

支持按年份或题号排除历史题，用于前向测试和同题泄漏检查：

```bash
python plugins/math-modeling-workbench/skills/mathmodel-rag/scripts/retrieve_modeling_kb.py \
  "需要预测未来需求，并在容量和风险约束下制定资源配置方案" \
  --top-k 12 \
  --exclude-year 2024 \
  --format prompt
```

## 论文与科研图表

内置 17 个竞赛模板族，每个模板同时提供 Typst 与 LaTeX 版本，覆盖中文、英文和主流数学建模赛事。数据图由可复现脚本生成，概念图和流程图保留可编辑源文件。

<table>
  <tr>
    <td align="center" width="33%">
      <img src="plugins/math-modeling-workbench/skills/mathmodel-figure-templates/assets/previews/paired_raincloud_replica.png" alt="配对云雨图" width="100%"><br>
      <sub>配对云雨图</sub>
    </td>
    <td align="center" width="33%">
      <img src="plugins/math-modeling-workbench/skills/mathmodel-figure-templates/assets/previews/taylor_diagram_replica.png" alt="泰勒图" width="100%"><br>
      <sub>多模型评价泰勒图</sub>
    </td>
    <td align="center" width="33%">
      <img src="plugins/math-modeling-workbench/skills/mathmodel-figure-templates/assets/previews/nature_chord_diagram_replica.png" alt="Nature 风格和弦图" width="100%"><br>
      <sub>Nature 风格和弦图</sub>
    </td>
  </tr>
</table>

除预制模板外，工作流还会根据实际问题生成预测诊断、误差分布、敏感性、Pareto 前沿、约束可行性和空间分析等论文图表。所有图表必须来自真实数据或明确标注的模拟数据。

<details>
<summary><strong>查看 v0.2.0 的准确性改进</strong></summary>

<br>

- 几何运动题检查连续首次接触、整条路径最小裕度、刚性长度和速度传播。
- 抽样检验明确原假设、备择假设、两类错误、OC / ASN，并审计可选停时。
- 返工和拆解决策使用闭合递归状态，验证最终吸收及成本只计一次。
- 多年种植规划逐项检查容量、适种、季间联动、重茬和滚动豆类约束，并从原始方案重算目标值。
- 公开论文或代码只有在单位、时间范围、统计口径和硬约束状态一致时才参与误差计算。
- 求解阶段生成统一结果证书，记录运行命令、数值指标、硬约束残差和同口径比较。

这些规则来自历史赛题的离线回放，但插件不内置评测题数值答案，避免把记忆旧答案误当成新题泛化能力。

</details>

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/youyou755939/MathModelingWorkbench.git
cd MathModelingWorkbench
```

### 2. 添加 Marketplace 并安装插件

```bash
codex plugin marketplace add .
codex plugin add math-modeling-workbench@math-modeling-workbench
```

安装后请新建一个 Codex 任务，使新的 Skills 被完整加载。

### 3. 开始建模

把赛题 PDF、数据附件或题目文本交给 Codex，然后直接描述目标：

```text
使用数学建模工作台完成这道赛题。先拆解问题并检索 RAG，
比较候选模型后运行可复现代码，最后生成 LaTeX 论文并完成提交前验收。
```

也可以只运行某个阶段：

| 需求 | 示例 |
| --- | --- |
| 只分析和选模 | `分析这道赛题，并用 RAG 比较候选模型。` |
| 只实现求解 | `根据建模报告实现代码，输出结果证书和论文图表。` |
| 只写论文 | `使用国赛 LaTeX 模板，根据现有结果撰写论文。` |
| 只做验收 | `检查这个数学建模项目是否具备提交条件。` |

## 目录结构

```text
MathModelingWorkbench/
├── .agents/plugins/marketplace.json
└── plugins/math-modeling-workbench/
    ├── .codex-plugin/plugin.json
    ├── assets/
    ├── scripts/
    └── skills/
        ├── 1start-mathmodel/
        ├── 2analysis-modeling/
        ├── 3coding-visual/
        ├── 4drawio/
        ├── 5writing/
        ├── 6verity/
        ├── mathmodel-rag/
        ├── mathmodel-figure-templates/
        ├── mathmodel-reference/
        ├── typst-author/
        └── doctor/
```

## 验证

验证插件结构、模板配对、RAG 数据库、稀疏索引和检索能力：

```bash
python plugins/math-modeling-workbench/scripts/validate_bundle.py
```

验证单次建模结果证书：

```bash
python plugins/math-modeling-workbench/scripts/validate_result_certificate.py \
  path/to/code/outputs/validation_certificate.json
```

通过时应看到：

```text
PASS manifest
PASS skills
PASS templates
PASS rag
PASS portability
PASS bundle
```

## 设计边界

- 历史题和算法卡用于提出候选结构，不是官方答案。
- 没有通过约束、复现和一致性检查的结果，不进入论文美化阶段。
- 插件不包含原 MathModelAgent 的 Vue / FastAPI Web 应用，只保留适合 Codex 调用的 Skills、知识库、模板和验收能力。
- 比赛年度规则可能变化，提交前仍应核对当年官方通知。

## License

[MIT](LICENSE)
