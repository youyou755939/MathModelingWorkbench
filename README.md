# Math Modeling Workbench

面向数学建模竞赛的 Codex 插件，覆盖赛题拆解、知识库检索、模型设计、可复现代码、科研图表、Typst/LaTeX 论文写作和提交前验收。

## 包含内容

- 完整数学建模工作流 Skills
- CUMCM 2000–2025 A/B/C 题及多项其他赛事的中文 RAG
- RAG 留出评测：可按年份或题号排除历史题，并检测同题信息泄漏
- Typst 与 LaTeX 竞赛论文模板
- 科研图表模板和绘图脚本
- 结果证书：统一记录运行命令、数值指标、硬约束残差和同口径比较
- 论文一致性、可复现性与提交就绪验收

## 0.2.0 的准确性改进

- 几何运动题要求连续首次接触、整条路径最小裕度、刚性长度和速度传播校验。
- 抽样检验要求明确原假设、备择假设、两类错误、OC/ASN，并审计可选停时。
- 返工和拆解决策要求闭合递归状态，验证最终吸收及成本只计一次。
- 多年种植规划要求逐项验证容量、适种、季间联动、重茬和滚动豆类约束，并从原始方案重算目标值。
- 公开论文或代码只有在单位、时间范围、统计口径和硬约束状态一致时才参与误差计算。

上述规则来自对历史赛题的离线回放，但插件不内置评测题的数值答案，避免把记忆旧答案误当成对新题的泛化能力。

## 安装

克隆本仓库：

```bash
git clone https://github.com/youyou755939/MathModelingWorkbench.git
cd MathModelingWorkbench
```

把仓库作为 Codex marketplace 添加，然后安装插件：

```bash
codex plugin marketplace add .
codex plugin add math-modeling-workbench@math-modeling-workbench
```

安装完成后新建一个 Codex 任务，并直接输入：

```text
使用数学建模工作台分析这道题，并检索 RAG。
```

## 本地验证

```bash
python plugins/math-modeling-workbench/scripts/validate_bundle.py
```

验证单次建模结果证书：

```bash
python plugins/math-modeling-workbench/scripts/validate_result_certificate.py path/to/validation_certificate.json
```

插件不包含原项目的 Vue/FastAPI Web 应用，只包含适合 Codex 直接调用的 Skills、知识库、模板和验收能力。

## License

MIT
