from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
EMOTION_CSV = ROOT / "13428_2021_1607_MOESM1_ESM.csv"
NORM_XLS = ROOT / "sj-xls-1-sgo-10.1177_21582440211054495.xls"
OUT_DIR = ROOT / "outputs" / "lexical_selection"


NEGATION_CHARS = set("不没无非未否勿莫甭")
DISEASE_HEALTH_CHARS = set("病疾癌症疫瘟疮疹瘤疼痛残瘫痴伤")
SENSITIVE_CONTEXT_CHARS = set("杀屠暴战枪毙炸灾震洪犯罪狱盗抢劫奸毒赌鸦亡死丧尸侵害")
NETWORK_WORDS = {
    "给力",
    "雷人",
    "屌丝",
    "宅男",
    "宅女",
    "网红",
    "吐槽",
    "囧",
    "卖萌",
    "点赞",
}
AMBIGUOUS_OR_CONTEXTUAL = {
    "黑暗",
    "落后",
    "过分",
    "完蛋",
    "开除",
    "封建",
    "魔鬼",
    "牢房",
    "监狱",
    "霸权",
    "政变",
    "民主",
    "合法",
    "军人",
    "烈士",
    "冠军",
    "第一",
    "妈妈",
    "亲人",
    "人才",
    "理想",
    "功劳",
    "榜样",
    "父爱",
    "奇迹",
    "安全",
    "住院",
    "抽烟",
    "蝗虫",
    "膨胀",
    "博士",
    "黎明",
    "正规",
    "有效",
    "增强",
    "前进",
    "兴趣",
    "响亮",
    "独特",
    "危机",
    "遭受",
    "投降",
    "惩罚",
    "批判",
    "坏处",
    "过失",
    "舒服",
    "妄想",
    "创新",
    "贡献",
    "成就",
    "模范",
    "吵架",
    "威胁",
    "强迫",
    "谣言",
    "逃避",
}

POSITIVE_POLARITY_ALLOWLIST = set(
    "鼓励 高尚 快乐 杰出 创新 诚实 荣誉 幸福 进步 勤劳 努力 积极 乐观 坚强 善良 忠诚 伟大 美德 灿烂 赞扬 欢乐 模范 称赞 胜利 信任 欢笑 表扬 出色 平安 愉快 奖励 自信 满意 坚定 爱护 可靠 踏实 赞美 纯洁 贡献 关怀 关心 勇气 信心 美丽 聪明 自豪 良心 礼貌 活泼 可爱 乐趣 友好 顺利 热情 成就 感动 刻苦 体贴 温柔 真诚 优美 亲切 和睦 勇敢 安慰 安宁 欢喜 安详 舒服"
    .split()
)

NEGATIVE_POLARITY_ALLOWLIST = set(
    "卑鄙 仇恨 绝望 侮辱 陷害 撒谎 阴谋 崩溃 欺骗 狭隘 倒霉 悲哀 恐惧 怒火 谣言 可恶 凶狠 说谎 消极 糟糕 吵架 强迫 愤怒 可怕 狠心 嘲笑 捏造 失败 烦躁 讽刺 荒谬 压抑 抱怨 狡猾 残酷 歪曲 妄想 逃避 焦急 惊慌 慌张 威胁 急躁 自私 虚伪 懒惰 冷漠 丑恶 悲观 胆怯 狂妄"
    .split()
)


def contains_any(word: str, chars: set[str]) -> bool:
    return any(char in word for char in chars)


def exclusion_reason(row: pd.Series) -> str:
    word = str(row["Word"])
    reasons: list[str] = []
    if len(word) != 2:
        reasons.append("非双字词")
    if contains_any(word, NEGATION_CHARS):
        reasons.append("含否定成分")
    if contains_any(word, DISEASE_HEALTH_CHARS):
        reasons.append("疾病/疼痛/损伤相关")
    if contains_any(word, SENSITIVE_CONTEXT_CHARS):
        reasons.append("暴力/犯罪/灾害/死亡等强情境词")
    if word in NETWORK_WORDS:
        reasons.append("网络词")
    if row.get("NOM", 99) > 2:
        reasons.append("外部常模义项数>2")
    if word in AMBIGUOUS_OR_CONTEXTUAL:
        reasons.append("明显多义或语境依赖")
    return "；".join(reasons)


def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(t), float(p)


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    return float((np.mean(a) - np.mean(b)) / pooled)


def summarize(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pos = selected[selected["Polarity"] == "positive"]
    neg = selected[selected["Polarity"] == "negative"]
    for col, label in [
        ("Valence_Mean", "效价"),
        ("Arousal_Mean", "唤醒度"),
        ("log_subTF", "log10字幕词频+1"),
        ("NOS", "总笔画数"),
        ("Familiarity", "熟悉度"),
    ]:
        t, p = welch(pos[col].to_numpy(), neg[col].to_numpy())
        rows.append(
            {
                "Variable": label,
                "Positive_Mean": pos[col].mean(),
                "Positive_SD": pos[col].std(ddof=1),
                "Negative_Mean": neg[col].mean(),
                "Negative_SD": neg[col].std(ddof=1),
                "Mean_Diff_PosMinusNeg": pos[col].mean() - neg[col].mean(),
                "Cohens_d": cohens_d(pos[col].to_numpy(), neg[col].to_numpy()),
                "Welch_t": t,
                "p": p,
            }
        )
    return pd.DataFrame(rows)


def objective(pos: pd.DataFrame, neg: pd.DataFrame, match_vars: list[str]) -> float:
    score = 0.0
    for col in match_vars:
        sd = np.std(pd.concat([pos[col], neg[col]]), ddof=1)
        smd = 0.0 if sd == 0 else (pos[col].mean() - neg[col].mean()) / sd
        score += smd * smd
    return float(score)


def random_search(pos_pool: pd.DataFrame, neg_pool: pd.DataFrame, seed: int = 20260602) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    rng = np.random.default_rng(seed)
    match_vars = ["log_subTF", "NOS", "Familiarity", "Arousal_Mean"]
    best_score = float("inf")
    best_pos = best_neg = None

    pos_idx = pos_pool.index.to_numpy()
    neg_idx = neg_pool.index.to_numpy()
    for _ in range(30_000):
        p_idx = rng.choice(pos_idx, 24, replace=False)
        n_idx = rng.choice(neg_idx, 24, replace=False)
        p_sel = pos_pool.loc[p_idx]
        n_sel = neg_pool.loc[n_idx]
        score = objective(p_sel, n_sel, match_vars)
        if score < best_score:
            best_score = score
            best_pos, best_neg = p_sel.copy(), n_sel.copy()

    assert best_pos is not None and best_neg is not None
    improved = True
    while improved:
        improved = False
        for polarity in ["positive", "negative"]:
            current_pos, current_neg = best_pos.copy(), best_neg.copy()
            pool = pos_pool if polarity == "positive" else neg_pool
            current = current_pos if polarity == "positive" else current_neg
            outside = pool.drop(index=current.index)
            for out_idx in outside.index:
                for in_idx in current.index:
                    trial = current.drop(index=in_idx)
                    trial = pd.concat([trial, pool.loc[[out_idx]]])
                    score = objective(trial, current_neg, match_vars) if polarity == "positive" else objective(current_pos, trial, match_vars)
                    if score + 1e-12 < best_score:
                        best_score = score
                        if polarity == "positive":
                            best_pos = trial.copy()
                        else:
                            best_neg = trial.copy()
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
    return best_pos, best_neg, best_score


def main() -> None:
    sys.path.insert(0, str(ROOT / ".codex_deps"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    emotion = pd.read_csv(EMOTION_CSV)
    norms = pd.read_excel(NORM_XLS).rename(columns={"2C-\nwords": "Word"})
    emotion["Word"] = emotion["Word"].astype(str).str.strip()
    norms["Word"] = norms["Word"].astype(str).str.strip()

    merged = emotion.merge(norms, on="Word", how="inner")
    merged["log_subTF"] = np.log10(merged["subTF"].astype(float) + 1)
    merged["Exclusion_Reason"] = merged.apply(exclusion_reason, axis=1)

    base = merged[
        (merged["Word"].str.len() == 2)
        & (merged["Exclusion_Reason"] == "")
        & (merged["Familiarity"] >= 4.5)
        & (merged["subTF"] >= 20)
        & (merged["Arousal_Mean"].between(1.70, 3.35))
    ].copy()
    pos_pool = base[(base["Valence_Mean"] >= 1.20) & (base["Word"].isin(POSITIVE_POLARITY_ALLOWLIST))].copy()
    neg_pool = base[(base["Valence_Mean"] <= -1.20) & (base["Word"].isin(NEGATIVE_POLARITY_ALLOWLIST))].copy()

    if len(pos_pool) < 24 or len(neg_pool) < 24:
        raise RuntimeError(f"Candidate pool too small: positive={len(pos_pool)}, negative={len(neg_pool)}")

    pos_sel, neg_sel, score = random_search(pos_pool, neg_pool)
    pos_sel["Polarity"] = "positive"
    neg_sel["Polarity"] = "negative"
    selected = pd.concat([pos_sel, neg_sel]).sort_values(["Polarity", "Word"])

    keep_cols = [
        "Polarity",
        "Word",
        "Valence_Mean",
        "Arousal_Mean",
        "subTF",
        "log_subTF",
        "NOS",
        "Familiarity",
        "NOM",
        "Valence_SD",
        "Valence_N",
        "Arousal_SD",
        "Arousal_N",
    ]
    selected[keep_cols].to_csv(OUT_DIR / "selected_emotion_words_24x2.csv", index=False, encoding="utf-8-sig")

    summary = summarize(selected)
    summary.to_csv(OUT_DIR / "selected_emotion_words_matching_summary.csv", index=False, encoding="utf-8-sig")

    candidates = merged.copy()
    candidates["Candidate_Status"] = "excluded"
    candidates.loc[pos_pool.index, "Candidate_Status"] = "positive_pool"
    candidates.loc[neg_pool.index, "Candidate_Status"] = "negative_pool"
    candidates.loc[selected.index, "Candidate_Status"] = "selected"
    candidates.to_csv(OUT_DIR / "emotion_words_merged_candidate_audit.csv", index=False, encoding="utf-8-sig")

    print(f"Merged words with Song & Li norms: {len(merged)}")
    print(f"Positive candidate pool: {len(pos_pool)}")
    print(f"Negative candidate pool: {len(neg_pool)}")
    print(f"Final objective score: {score:.6f}")
    print(summary.to_string(index=False))
    print(selected[keep_cols].to_string(index=False))


if __name__ == "__main__":
    main()
