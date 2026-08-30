# Math Modeling Workbench

面向数学建模竞赛的 Codex 插件，覆盖赛题拆解、知识库检索、模型设计、可复现代码、科研图表、Typst/LaTeX 论文写作和提交前验收。

## 包含内容

- 完整数学建模工作流 Skills
- CUMCM 2000–2025 A/B/C 题及多项其他赛事的中文 RAG
- Typst 与 LaTeX 竞赛论文模板
- 科研图表模板和绘图脚本
- 论文一致性、可复现性与提交就绪验收

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

插件不包含原项目的 Vue/FastAPI Web 应用，只包含适合 Codex 直接调用的 Skills、知识库、模板和验收能力。

## License

MIT
