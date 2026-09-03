"""Factorial statistics for the educational-text evaluation study.

SciPy and statsmodels perform the established calculations. This code does not
claim to derive or reimplement ANOVA mathematically.
"""
from __future__ import annotations

import argparse
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_excel(path) if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(path)


def validate_columns(
    frame: pd.DataFrame,
    factor_a: str,
    factor_b: str,
    run_column: str,
    outcomes: list[str],
) -> pd.DataFrame:
    requested = [factor_a, factor_b, run_column, *outcomes]
    unsafe = [name for name in requested if not IDENTIFIER.match(name)]
    if unsafe:
        raise ValueError(f"Column names must be formula-safe identifiers: {unsafe}")
    missing = [column for column in requested if column not in frame.columns]
    if missing:
        raise ValueError(f"Input data is missing columns: {missing}")
    result = frame.copy()
    for outcome in outcomes:
        result[outcome] = pd.to_numeric(result[outcome], errors="coerce")
        if result[outcome].notna().sum() < 3:
            raise ValueError(f"Outcome {outcome!r} has fewer than three numeric observations")
    if result[[factor_a, factor_b]].isna().any().any():
        raise ValueError("Factor columns cannot contain missing values")
    return result


def descriptive_statistics(
    frame: pd.DataFrame, factor_a: str, factor_b: str, outcomes: list[str]
) -> pd.DataFrame:
    return frame.groupby([factor_a, factor_b], dropna=False)[outcomes].agg(
        ["count", "mean", "std", "median", "min", "max"]
    ).reset_index()


def two_way_anova(
    frame: pd.DataFrame, outcome: str, factor_a: str, factor_b: str
) -> tuple[pd.DataFrame, object]:
    subset = frame[[outcome, factor_a, factor_b]].dropna()
    model = ols(f"{outcome} ~ C({factor_a}) * C({factor_b})", data=subset).fit()
    table = anova_lm(model, typ=2).reset_index().rename(
        columns={"index": "effect", "PR(>F)": "p_value", "F": "F_value"}
    )
    residual_ss = float(table.loc[table["effect"] == "Residual", "sum_sq"].iloc[0])
    table["partial_eta_squared"] = np.where(
        table["effect"].eq("Residual"),
        np.nan,
        table["sum_sq"] / (table["sum_sq"] + residual_ss),
    )
    table.insert(0, "outcome", outcome)
    return table, model


def assumption_checks(
    frame: pd.DataFrame, model: object, outcome: str, factor_a: str, factor_b: str
) -> dict[str, object]:
    residuals = pd.Series(model.resid).dropna()  # type: ignore[attr-defined]
    shapiro_w = shapiro_p = np.nan
    if 3 <= len(residuals) <= 5000:
        shapiro = stats.shapiro(residuals)
        shapiro_w, shapiro_p = float(shapiro.statistic), float(shapiro.pvalue)
    groups = [
        group[outcome].dropna().to_numpy()
        for _, group in frame.groupby([factor_a, factor_b], sort=False)
        if group[outcome].notna().sum() >= 2
    ]
    levene_f = levene_p = np.nan
    if len(groups) >= 2:
        levene = stats.levene(*groups, center="median")
        levene_f, levene_p = float(levene.statistic), float(levene.pvalue)
    return {
        "outcome": outcome,
        "residual_n": len(residuals),
        "shapiro_w": shapiro_w,
        "shapiro_p_value": shapiro_p,
        "levene_F_value": levene_f,
        "levene_p_value": levene_p,
    }


def tukey_comparisons(
    frame: pd.DataFrame, outcome: str, factor_a: str, factor_b: str
) -> pd.DataFrame:
    """Compare factor-A levels overall and within each factor-B level."""
    records: list[pd.DataFrame] = []
    for scope, level, subset in [("overall", "ALL", frame), *[
        (f"within_{factor_b}", str(level), group)
        for level, group in frame.groupby(factor_b, sort=False)
    ]]:
        data = subset[[outcome, factor_a]].dropna()
        if data[factor_a].nunique() < 2:
            continue
        result = pairwise_tukeyhsd(data[outcome], data[factor_a])
        table = pd.DataFrame(result._results_table.data[1:], columns=result._results_table.data[0])
        table.insert(0, "scope", scope)
        table.insert(1, factor_b, level)
        records.append(table)
    combined = pd.concat(records, ignore_index=True) if records else pd.DataFrame()
    if not combined.empty:
        combined.insert(0, "outcome", outcome)
    return combined


def run_sensitivity(
    frame: pd.DataFrame,
    outcome: str,
    factor_a: str,
    factor_b: str,
    run_column: str,
) -> pd.DataFrame:
    """Add Run as a categorical factor and check whether conclusions remain stable."""
    subset = frame[[outcome, factor_a, factor_b, run_column]].dropna()
    model = ols(
        f"{outcome} ~ C({factor_a}) * C({factor_b}) + C({run_column})",
        data=subset,
    ).fit()
    table = anova_lm(model, typ=2).reset_index().rename(
        columns={"index": "effect", "PR(>F)": "p_value", "F": "F_value"}
    )
    table.insert(0, "outcome", outcome)
    return table


def correlation_table(frame: pd.DataFrame, outcomes: list[str]) -> pd.DataFrame:
    rows = []
    for left, right in combinations(outcomes, 2):
        complete = frame[[left, right]].dropna()
        if len(complete) < 3 or complete[left].nunique() < 2 or complete[right].nunique() < 2:
            coefficient = p_value = np.nan
        else:
            result = stats.pearsonr(complete[left], complete[right])
            coefficient, p_value = float(result.statistic), float(result.pvalue)
        rows.append({"metric_a": left, "metric_b": right, "n": len(complete), "pearson_r": coefficient, "p_value": p_value})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the educational-text factorial analysis.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--outcomes", nargs="+", default=["Lexile", "FKGL"])
    parser.add_argument("--factor-a", default="System")
    parser.add_argument("--factor-b", default="Chapter")
    parser.add_argument("--run-column", default="Run")
    args = parser.parse_args(argv)
    data = validate_columns(read_table(args.input), args.factor_a, args.factor_b, args.run_column, args.outcomes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    anova_tables, tukey_tables, sensitivity_tables, assumptions = [], [], [], []
    for outcome in args.outcomes:
        anova, model = two_way_anova(data, outcome, args.factor_a, args.factor_b)
        anova_tables.append(anova)
        assumptions.append(assumption_checks(data, model, outcome, args.factor_a, args.factor_b))
        tukey = tukey_comparisons(data, outcome, args.factor_a, args.factor_b)
        if not tukey.empty:
            tukey_tables.append(tukey)
        sensitivity_tables.append(run_sensitivity(data, outcome, args.factor_a, args.factor_b, args.run_column))
    pd.concat(anova_tables, ignore_index=True).to_csv(args.output_dir / "two_way_anova.csv", index=False)
    pd.DataFrame(assumptions).to_csv(args.output_dir / "assumption_checks.csv", index=False)
    if tukey_tables:
        pd.concat(tukey_tables, ignore_index=True).to_csv(args.output_dir / "tukey_hsd.csv", index=False)
    pd.concat(sensitivity_tables, ignore_index=True).to_csv(args.output_dir / "run_sensitivity.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
