"""Statistics for the bilingual model/domain/prompt study.

The factorial analysis is primary. The paired function is supplementary and
belongs to a different two-condition design.
"""
from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(name: str) -> str:
    if not IDENTIFIER.match(name):
        raise ValueError(f"Column name must be formula-safe: {name!r}")
    return name


def factorial_anova(
    frame: pd.DataFrame,
    outcome: str,
    model: str = "model",
    domain: str = "domain",
    prompt: str = "prompt",
    include_two_way_interactions: bool = False,
) -> tuple[pd.DataFrame, object]:
    """Fit Type II ANOVA for model, domain, and prompt.

    The default additive model reports the three main effects shown in the
    study summary. Two-way interactions can be included when justified by the
    design. A saturated three-way interaction is intentionally not fitted by
    default because one full-text observation per cell leaves no replication.
    """
    columns = [_safe_identifier(name) for name in [outcome, model, domain, prompt]]
    missing = [name for name in columns if name not in frame.columns]
    if missing:
        raise ValueError(f"Input is missing columns: {missing}")
    subset = frame[columns].dropna().copy()
    subset[outcome] = pd.to_numeric(subset[outcome], errors="coerce")
    subset = subset.dropna(subset=[outcome])
    base = f"C({model}) + C({domain}) + C({prompt})"
    if include_two_way_interactions:
        base += f" + C({model}):C({domain}) + C({model}):C({prompt}) + C({domain}):C({prompt})"
    fitted = ols(f"{outcome} ~ {base}", data=subset).fit()
    table = anova_lm(fitted, typ=2).reset_index().rename(
        columns={"index": "effect", "F": "F_value", "PR(>F)": "p_value"}
    )
    residual_ss = float(table.loc[table["effect"] == "Residual", "sum_sq"].iloc[0])
    table["partial_eta_squared"] = np.where(
        table["effect"].eq("Residual"),
        np.nan,
        table["sum_sq"] / (table["sum_sq"] + residual_ss),
    )
    table.insert(0, "outcome", outcome)
    return table, fitted


def tukey_posthoc(frame: pd.DataFrame, outcome: str, factor: str) -> pd.DataFrame:
    """Run Tukey HSD for one selected factor after a multi-group analysis."""
    _safe_identifier(outcome)
    _safe_identifier(factor)
    if outcome not in frame.columns or factor not in frame.columns:
        raise ValueError("Outcome or factor column is missing")
    subset = frame[[outcome, factor]].dropna().copy()
    subset[outcome] = pd.to_numeric(subset[outcome], errors="coerce")
    subset = subset.dropna()
    if subset[factor].nunique() < 2:
        raise ValueError("Tukey HSD requires at least two factor levels")
    result = pairwise_tukeyhsd(subset[outcome], subset[factor])
    table = pd.DataFrame(result._results_table.data[1:], columns=result._results_table.data[0])
    table.insert(0, "outcome", outcome)
    table.insert(1, "factor", factor)
    return table


def supplementary_paired_comparison(
    frame: pd.DataFrame,
    outcome: str,
    id_column: str = "text_id",
    condition_column: str = "condition",
) -> dict[str, object]:
    """Compare exactly two matched conditions; not the cross-model paper design."""
    required = [id_column, condition_column, outcome]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Paired input is missing columns: {missing}")
    if frame[condition_column].nunique() != 2:
        raise ValueError("Paired comparison requires exactly two conditions")
    wide = frame.pivot(index=id_column, columns=condition_column, values=outcome).dropna()
    if len(wide) < 2:
        raise ValueError("Paired comparison requires at least two complete pairs")
    left_name, right_name = list(wide.columns)
    left = pd.to_numeric(wide[left_name], errors="coerce")
    right = pd.to_numeric(wide[right_name], errors="coerce")
    complete = pd.DataFrame({"left": left, "right": right}).dropna()
    differences = complete["right"] - complete["left"]
    t_result = stats.ttest_rel(complete["right"], complete["left"])
    standard_error = stats.sem(differences)
    if len(differences) > 1 and standard_error > 0:
        ci_low, ci_high = stats.t.interval(
            0.95, len(differences) - 1, loc=differences.mean(), scale=standard_error
        )
    else:
        ci_low = ci_high = math.nan
    dz = differences.mean() / differences.std(ddof=1) if differences.std(ddof=1) else math.nan
    wilcoxon_stat = wilcoxon_p = math.nan
    if not np.allclose(differences, 0):
        wilcoxon = stats.wilcoxon(differences)
        wilcoxon_stat, wilcoxon_p = float(wilcoxon.statistic), float(wilcoxon.pvalue)
    return {
        "analysis_scope": "supplementary_paired_two_condition_utility",
        "condition_a": left_name,
        "condition_b": right_name,
        "n_pairs": len(complete),
        "mean_difference_b_minus_a": float(differences.mean()),
        "paired_t": float(t_result.statistic),
        "paired_t_p_value": float(t_result.pvalue),
        "difference_ci_95_low": float(ci_low),
        "difference_ci_95_high": float(ci_high),
        "cohen_dz": float(dz),
        "wilcoxon_statistic": wilcoxon_stat,
        "wilcoxon_p_value": wilcoxon_p,
    }
