"""Merge text-level outcomes and conduct paired, auditable statistics."""
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from common import OUTPUTS, load_config, read_excel, setup_logging


def safe_name(value: str) -> str:
    """Create a filesystem-safe metric name."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def plot_diagnostics(metric: str, wide: pd.DataFrame, a: str, b: str, figure_dir: Path) -> None:
    """Save paired line, paired-difference histogram, Q-Q, and boxplot figures."""
    difference = wide[b] - wide[a]
    fig, ax = plt.subplots()
    for _, row in wide.iterrows(): ax.plot([a, b], [row[a], row[b]], marker="o")
    ax.set_ylabel(metric); ax.set_title(f"Paired values: {metric}"); fig.tight_layout()
    fig.savefig(figure_dir / f"{safe_name(metric)}_paired.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(); ax.hist(difference.dropna()); ax.set_title(f"Paired differences (B - A): {metric}"); fig.tight_layout()
    fig.savefig(figure_dir / f"{safe_name(metric)}_differences.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(); stats.probplot(difference.dropna(), dist="norm", plot=ax); ax.set_title(f"Q-Q: {metric}"); fig.tight_layout()
    fig.savefig(figure_dir / f"{safe_name(metric)}_qq.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(); ax.boxplot(difference.dropna()); ax.set_title(f"Difference boxplot: {metric}"); fig.tight_layout()
    fig.savefig(figure_dir / f"{safe_name(metric)}_boxplot.png", dpi=160); plt.close(fig)


def analyze(metric: str, data: pd.DataFrame, a: str, b: str, low_n: int, figure_dir: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    """Analyze one metric using independent complete text pairs only."""
    wide = data.pivot(index="text_id", columns="condition", values=metric)
    if a not in wide or b not in wide:
        return {"metric": metric, "error": "Configured condition missing"}, pd.DataFrame()
    wide = wide[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    difference = wide[b] - wide[a]; n = len(wide)
    if n < 2:
        return {"metric": metric, "n_pairs": n, "error": "Fewer than 2 complete pairs"}, pd.DataFrame()
    mean_diff = difference.mean(); sd_diff = difference.std(ddof=1); se = sd_diff / np.sqrt(n)
    t_result = stats.ttest_rel(wide[b], wide[a], nan_policy="omit")
    shapiro = stats.shapiro(difference) if 3 <= n <= 5000 else None
    ci = stats.t.interval(0.95, n - 1, loc=mean_diff, scale=se) if se > 0 else (mean_diff, mean_diff)
    q1, q3 = difference.quantile([.25, .75]); iqr = q3 - q1
    outlier = (difference < q1 - 1.5 * iqr) | (difference > q3 + 1.5 * iqr)
    wilcoxon_stat = wilcoxon_p = np.nan
    if shapiro is not None and shapiro.pvalue < .05 and np.any(difference != 0):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore"); result = stats.wilcoxon(difference, alternative="two-sided")
        wilcoxon_stat, wilcoxon_p = result.statistic, result.pvalue
    result_row = {"metric": metric, "n_pairs": n, "condition_a": a, "condition_a_mean": wide[a].mean(),
                  "condition_a_sd": wide[a].std(ddof=1), "condition_b": b, "condition_b_mean": wide[b].mean(),
                  "condition_b_sd": wide[b].std(ddof=1), "mean_difference_b_minus_a": mean_diff,
                  "sd_paired_differences": sd_diff, "ci95_lower": ci[0], "ci95_upper": ci[1],
                  "paired_t": t_result.statistic, "df": n - 1, "p_two_sided": t_result.pvalue,
                  "cohens_dz": mean_diff / sd_diff if sd_diff else np.nan,
                  "positive_differences": int((difference > 0).sum()), "negative_differences": int((difference < 0).sum()),
                  "zero_differences": int((difference == 0).sum()), "shapiro_w": shapiro.statistic if shapiro else np.nan,
                  "shapiro_p": shapiro.pvalue if shapiro else np.nan, "wilcoxon_statistic": wilcoxon_stat,
                  "wilcoxon_p_two_sided": wilcoxon_p, "iqr_outlier_count": int(outlier.sum()),
                  "low_statistical_power_warning": n < low_n}
    detail = wide.reset_index(); detail["metric"] = metric; detail["difference_b_minus_a"] = difference.values; detail["iqr_outlier"] = outlier.values
    plot_diagnostics(metric, wide, a, b, figure_dir)
    return result_row, detail


def main() -> int:
    """Merge score files, verify pairs, run tests, adjust secondary p-values, and plot."""
    logger = setup_logging("statistics", "statistics.log")
    try:
        config = load_config(); a, b = str(config["condition_a"]), str(config["condition_b"])
        validated = read_excel(OUTPUTS / "validated_data.xlsx", "data")
        comet = read_excel(OUTPUTS / "comet_text_scores.xlsx", "Sheet1")
        metrics = read_excel(OUTPUTS / "text_metrics.xlsx", "Sheet1")
        keys = ["text_id", "condition"]
        if any(frame.duplicated(keys).any() for frame in (validated, comet, metrics)):
            raise ValueError("Duplicate text_id + condition detected; statistics require one text-level row per condition")
        expected = validated.groupby("text_id")["condition"].apply(set)
        incomplete = expected[~expected.map(lambda values: {a, b}.issubset(values))]
        if not incomplete.empty: raise ValueError(f"Incomplete configured pairs for text_id: {incomplete.index.tolist()}")
        merged = validated.merge(comet[keys + ["comet_score"]], on=keys, how="left").merge(metrics, on=keys, how="left")
        OUTPUTS.mkdir(parents=True, exist_ok=True); figure_dir = OUTPUTS / "figures"; figure_dir.mkdir(exist_ok=True)
        merged.to_excel(OUTPUTS / "merged_scores.xlsx", index=False)
        candidates = ["comet_score", "fkgl_output", "fkgl_absolute_deviation", "l2_readability",
                      "referential_cohesion", "deep_cohesion", "adjacent_content_word_overlap_output",
                      "connective_total_incidence_output"]
        available = [metric for metric in candidates if metric in merged.columns and pd.to_numeric(merged[metric], errors="coerce").notna().any()]
        if "comet_score" not in available: raise ValueError("Primary COMET outcome is unavailable; run 02_run_comet.py successfully")
        results, details = [], []
        for metric in available:
            row, detail = analyze(metric, merged[keys + [metric]], a, b, int(config.get("low_power_n_threshold", 20)), figure_dir)
            row["outcome_role"] = "primary" if metric == "comet_score" else "secondary_or_exploratory"
            results.append(row)
            if not detail.empty: details.append(detail)
        result_frame = pd.DataFrame(results)
        secondary = (result_frame["outcome_role"] != "primary") & result_frame["p_two_sided"].notna()
        result_frame["holm_adjusted_p"] = np.nan
        if secondary.any(): result_frame.loc[secondary, "holm_adjusted_p"] = multipletests(result_frame.loc[secondary, "p_two_sided"], method="holm")[1]
        descriptive_columns = [c for c in result_frame if c in {"metric", "n_pairs", "condition_a", "condition_a_mean", "condition_a_sd", "condition_b", "condition_b_mean", "condition_b_sd", "mean_difference_b_minus_a", "sd_paired_differences"}]
        result_frame[descriptive_columns].to_excel(OUTPUTS / "descriptive_statistics.xlsx", index=False)
        result_frame.to_excel(OUTPUTS / "paired_test_results.xlsx", index=False)
        pd.concat(details, ignore_index=True).to_excel(OUTPUTS / "pairwise_differences.xlsx", index=False)
        low = result_frame[result_frame["low_statistical_power_warning"] == True]
        if not low.empty: logger.warning("LOW STATISTICAL POWER: n_pairs below configured threshold for: %s", low["metric"].tolist())
        logger.info("Statistics complete for %d metric(s). p > .05 is not interpreted as 'no effect'.", len(result_frame))
        return 0
    except Exception as exc:
        logger.exception("Merge/statistics failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
