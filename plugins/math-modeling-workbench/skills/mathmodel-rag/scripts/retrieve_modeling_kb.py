from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


HERE = Path(__file__).resolve().parent
DEFAULT_KB = HERE.parent / "references" / "kb"
LATIN = re.compile(r"[a-z]+(?:[-_/][a-z0-9]+)*|\d+(?:\.\d+)?", re.I)
CHINESE = re.compile(r"[\u4e00-\u9fff]+")


EXPANSIONS = {
    "预测": "回归 时间序列 ARIMA 灰色模型 滚动验证 区间预测",
    "销量": "需求 预测 时间序列 价格弹性 补货 库存",
    "需求": "预测 回归 时间序列 库存 资源配置",
    "评价": "指标体系 权重 熵权 CRITIC AHP TOPSIS 稳定排序",
    "排名": "综合评价 TOPSIS 权重 排序稳定性",
    "分类": "Logistic LDA SVM 随机森林 XGBoost F1 ROC-AUC",
    "识别": "分类 特征工程 SVM 随机森林 混淆矩阵",
    "异常": "分类 风险 阈值 校准 ROC 代价敏感",
    "聚类": "K-means 层次聚类 GMM DBSCAN 轮廓系数",
    "画像": "RFM 聚类 生命周期 关联规则",
    "优化": "决策变量 目标函数 约束 基线 可行性 敏感性",
    "调度": "整数规划 动态规划 排队 离散事件仿真 鲁棒优化",
    "路径": "图论 Dijkstra A* TSP VRP 网络流",
    "选址": "设施选址 p-median 集合覆盖 整数规划",
    "资源": "线性规划 整数规划 分配 多目标优化",
    "多目标": "Pareto 权重法 epsilon约束 NSGA-II 敏感性",
    "不确定": "Monte Carlo Bootstrap 鲁棒优化 随机规划 CVaR",
    "风险": "概率 分类 生存分析 CVaR 敏感性 校准",
    "传播": "SIR SEIR 微分方程 参数辨识 Monte Carlo",
    "传热": "PDE 有限差分 有限元 边界条件 网格收敛",
    "动力学": "ODE 状态方程 数值积分 参数辨识 稳定性",
    "控制": "PID MPC 最优控制 状态空间 扰动",
    "定位": "坐标变换 三角定位 非线性最小二乘 误差传播",
    "成像": "Radon FBP 正则化 逆问题 重建误差",
    "颜色": "CIE1931 XYZ xyY CIELAB CIEDE2000 白点 白平衡 色域映射 感知色差",
    "色域": "BT2020 sRGB RGBV RGBCX 多基色 凸包 三角剖分 有界优化 gamut mapping",
    "显示": "LED EOTF gamma 设备响应矩阵 白平衡 色域映射 实时LUT",
    "多基色": "伪逆 零空间 非负有界二次规划 功耗 通道均衡 同色异谱",
    "校正": "逐像素 响应矩阵 共同可达色域 条件数 正则化 坏点 均匀度",
    "白平衡": "D65 中性轴 黑白点锚定 基色对应 neutral axis",
    "几何": "坐标变换 解析几何 碰撞检测 非线性优化",
    "排队": "排队论 离散事件仿真 等待时间 吞吐量",
    "交通": "图论 路径 元胞自动机 排队 仿真 调度 多源融合 网络韧性 可达率",
    "韧性": "随机失效 场景采样 可达率 CVaR 网络设计 多商品流",
    "图着色": "冲突图 加权图着色 DSATUR 词典序 禁忌搜索 边界效应",
    "微电网": "风光储 功率平衡 SOC 容量配置 弃风弃光 全寿命成本 MILP",
    "储能": "SOC 充放电效率 功率容量 年化投资 典型日 鲁棒调度",
    "推荐": "list-wise 序列收益 点击 时长 位置偏差 多任务 剪枝 精排",
    "分割": "图像预处理 U-Net IoU Dice 过切 粘连 OCR 端到端",
    "临床": "患者级划分 小样本 概率校准 纵向数据 治疗混杂 决策曲线",
    "纵向": "混合效应 GAM 轨迹聚类 不规则随访 患者级交叉验证",
    "药物": "QSAR 分子描述符 嵌套交叉验证 ADMET 适用域 Pareto",
    "组批": "二维装箱 齐头切 排样 列生成 下界 批次容量",
    "切割": "计算几何 齐头切 GTSP 嵌套先后 过桥 空程",
    "多源": "时空对齐 观测方程 状态空间 源可靠度 留源消融 数据融合",
    "实验": "ANOVA 响应面 正交设计 贝叶斯优化 信息增益",
    "敏感性": "参数扰动 Sobol Bootstrap 稳健性",
    "验证": "基线 交叉验证 滚动验证 残差 消融 置信区间",
}


def compact(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def tokenize(text: str) -> list[str]:
    text = compact(text).lower().replace("—", "-")
    out = LATIN.findall(text)
    for seq in CHINESE.findall(text):
        if len(seq) <= 8:
            out.append(seq)
        out.extend(seq[i:i + 2] for i in range(len(seq) - 1))
        if len(seq) >= 3:
            out.extend(seq[i:i + 3] for i in range(len(seq) - 2))
    return out


def expand_query(query: str) -> tuple[str, list[str]]:
    hits = []
    additions = []
    low = query.lower()
    for signal, terms in EXPANSIONS.items():
        if signal.lower() in low:
            hits.append(signal)
            additions.append(terms)
    return query + " " + " ".join(additions), hits


def load_kb(kb_dir: Path) -> tuple[list[dict], dict]:
    with (kb_dir / "chunks.jsonl").open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f if line.strip()]
    with gzip.open(kb_dir / "retrieval_index.json.gz", "rt", encoding="utf-8") as f:
        index = json.load(f)
    return chunks, index


def bm25_scores(query: str, chunks: list[dict], index: dict) -> tuple[dict[str, float], list[str]]:
    expanded, expansion_hits = expand_query(query)
    qtf = Counter(tokenize(expanded))
    avgdl = index["average_length"]
    k1, b = 1.45, 0.72
    scores = {}
    for ch in chunks:
        cid = ch["chunk_id"]
        tf = index["doc_tf"][cid]
        dl = index["doc_len"][cid]
        score = 0.0
        for term, q_count in qtf.items():
            freq = tf.get(term, 0)
            if not freq:
                continue
            idf = index["idf"].get(term, 0.0)
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf * (freq * (k1 + 1) / denom) * min(1.6, 1 + 0.12 * (q_count - 1))

        meta = ch["metadata"]
        exact_zone = " ".join([
            ch["title"], compact(meta.get("problem_type")), compact(meta.get("domain")),
            compact(meta.get("algorithms")), " ".join(ch["tags"])
        ]).lower()
        for signal in expansion_hits:
            if signal.lower() in exact_zone:
                score += 1.8
        for raw in re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z][a-zA-Z0-9_-]+", query):
            if raw.lower() in exact_zone:
                score += 2.2
        score *= float(ch.get("priority", 1.0))
        scores[cid] = score
    return scores, expansion_hits


def diversified_rank(chunks: list[dict], scores: dict[str, float], top_k: int) -> list[dict]:
    ordered = sorted(chunks, key=lambda c: scores.get(c["chunk_id"], 0.0), reverse=True)
    buckets = defaultdict(list)
    for ch in ordered:
        if scores.get(ch["chunk_id"], 0) > 0:
            buckets[ch["chunk_type"]].append(ch)

    overview_quota = 2 if top_k >= 12 else 1
    algorithm_quota = 2
    strategy_quota = 2
    case_quota = max(1, top_k - overview_quota - algorithm_quota - strategy_quota)
    quotas = {
        "case_subquestion": case_quota,
        "problem_overview": overview_quota,
        "algorithm_card": algorithm_quota,
        "strategy_card": strategy_quota,
    }
    selected, used = [], set()
    for kind, quota in quotas.items():
        problem_seen = set()
        for ch in buckets[kind]:
            if len([x for x in selected if x["chunk_type"] == kind]) >= quota:
                break
            problem_key = (ch["metadata"].get("year"), ch["metadata"].get("problem"))
            if kind == "case_subquestion" and problem_key in problem_seen and len(buckets[kind]) > quota:
                continue
            selected.append(ch)
            used.add(ch["chunk_id"])
            problem_seen.add(problem_key)
    for ch in ordered:
        if len(selected) >= top_k:
            break
        if ch["chunk_id"] not in used and scores.get(ch["chunk_id"], 0) > 0:
            selected.append(ch)
            used.add(ch["chunk_id"])
    selected.sort(key=lambda c: scores[c["chunk_id"]], reverse=True)
    return selected[:top_k]


def render_prompt(query: str, results: list[dict], scores: dict[str, float], expansion_hits: list[str]) -> str:
    lines = [
        "# 数学建模竞赛新题求解 RAG 上下文包",
        "",
        f"用户新题/查询：{query}",
        f"检索扩展信号：{'、'.join(expansion_hits) if expansion_hits else '无；按原查询检索'}",
        "",
        "## 使用约束",
        "",
        "1. 历史题仅用于结构类比，不可把题名相似当成模型正确。",
        "2. 先提取对象、变量、数据结构、目标和约束，再选择基线与升级模型。",
        "3. 推荐算法不是唯一官方答案；必须结合本题数据做验证、敏感性与可行性检查。",
        "4. 输出应覆盖：问题重述、假设、符号、模型、求解、评价、稳健性、局限与结论。",
        "5. 来源等级决定证据权重：官方题面/官方解析优先；公开论文或代码只作候选方法，不能替代本题验证。",
        "",
        "## 检索证据",
        "",
    ]
    for i, ch in enumerate(results, 1):
        m = ch["metadata"]
        lines.extend([
            f"### R{i} [{ch['chunk_id']}] {ch['title']}",
            f"- 类型：{ch['chunk_type']}；相关分：{scores[ch['chunk_id']]:.3f}",
            f"- 问题类型/领域：{compact(m.get('problem_type'))} / {compact(m.get('domain'))}",
            f"- 候选算法：{compact(m.get('algorithms'))}",
            f"- 建模流程：{compact(m.get('workflow'))}",
            f"- 评价指标：{compact(m.get('metrics'))}",
            f"- 模型假设：{compact(m.get('assumptions'))}",
            f"- 灵敏度/稳健性：{compact(m.get('sensitivity'))}",
            f"- 写作范式：{compact(m.get('writing_pattern'))}",
            f"- 关键风险：{compact(m.get('cautions'))}",
            f"- 来源审计：{compact(m.get('source_grade'))}；{compact(m.get('verification'))}",
            f"- 证据摘要：{ch['content']}",
            "",
        ])
    lines.extend([
        "## 建议的回答生成顺序",
        "",
        "题意结构识别 → 历史类比及差异 → 基线模型 → 候选升级模型 → 数学表达与求解 → 验证指标 → 鲁棒性/敏感性 → 论文输出清单。",
    ])
    return "\n".join(lines)


def retrieve(query: str, kb_dir: Path, top_k: int) -> tuple[list[dict], dict[str, float], list[str]]:
    chunks, index = load_kb(kb_dir)
    scores, expansion_hits = bm25_scores(query, chunks, index)
    return diversified_rank(chunks, scores, top_k), scores, expansion_hits


def main() -> None:
    p = argparse.ArgumentParser(description="检索 CUMCM 2000-2025 新题求解 RAG 知识库")
    p.add_argument("query", help="新题描述、某个小问或希望寻找的模型")
    p.add_argument("--kb", type=Path, default=DEFAULT_KB, help="知识库目录")
    p.add_argument("--top-k", type=int, default=12, help="返回知识块数量")
    p.add_argument("--format", choices=["prompt", "json", "brief"], default="prompt")
    p.add_argument("--out", type=Path, help="把结果写入文件")
    args = p.parse_args()

    results, scores, hits = retrieve(args.query, args.kb, max(4, args.top_k))
    if args.format == "json":
        payload = {
            "query": args.query,
            "expansion_hits": hits,
            "results": [{**ch, "score": scores[ch["chunk_id"]]} for ch in results],
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "brief":
        text = "\n".join(
            f"{i}. {ch['title']} | {ch['chunk_type']} | {scores[ch['chunk_id']]:.3f} | {ch['metadata'].get('algorithms','')}"
            for i, ch in enumerate(results, 1)
        )
    else:
        text = render_prompt(args.query, results, scores, hits)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
