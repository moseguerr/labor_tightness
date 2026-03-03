"""
Exposure-Robust Inference for Bartik IV (BHJ 2022 ssaggregate)
================================================================

Implements the Borusyak, Hull & Jaravel (2022) "ssaggregate" procedure:
1. Estimate the MSA-level regression at the observation level
2. Residualize Y and X from controls + FE
3. Aggregate residualized Y and X to the shock level using exposure weights
4. Run the shock-level regression with exposure-robust SEs

This produces valid SEs when shocks (not shares) provide identification.
The standard approach clusters on MSA, but with few effective shocks,
shock-level clustering (or Herfindahl-based adjustment) is more appropriate.

Reference: BHJ (2022) Section 4.3, Algorithm 1

Output: data/bartik/diagnostics/ssaggregate_results.csv
"""

import pandas as pd
import numpy as np
import os
import gc
import statsmodels.api as sm

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
OUT_DIR = os.path.join(DATA_DIR, "bartik", "diagnostics")
os.makedirs(OUT_DIR, exist_ok=True)


def load_bartik_components():
    """Load industry-level Bartik components (shares × shifts)."""
    path = os.path.join(DATA_DIR, "bartik", "bartik_components.parquet")
    return pd.read_parquet(path, engine="fastparquet")


def load_bartik_instrument():
    """Load the aggregated Bartik instrument."""
    path = os.path.join(DATA_DIR, "bartik", "bartik_instrument.parquet")
    return pd.read_parquet(path, engine="fastparquet")


def load_unemployment():
    """Load MSA-level unemployment rates from LAUS."""
    path = os.path.join(DATA_DIR, "LAUS", "LAUS_msa.csv")
    df = pd.read_csv(path)
    df["unemploymentRate_msa"] = pd.to_numeric(df["unemploymentRate_msa"], errors="coerce")

    # Quarterly average
    df = df.rename(columns={"Year": "year"})
    df["qtr"] = ((df["Month"] - 1) // 3) + 1
    quarterly = df.groupby(["BestFitMSA", "year", "qtr"], as_index=False).agg(
        unemp_quarter=("unemploymentRate_msa", "mean")
    )
    # LAUS BestFitMSA is 5-digit CBSA; Bartik BestFitMSA4 is 4-digit QCEW
    quarterly["BestFitMSA4"] = quarterly["BestFitMSA"] // 10
    quarterly = quarterly.drop(columns=["BestFitMSA"])
    return quarterly


def demean_by_group(df, col, group_col):
    """Remove group means (equivalent to absorbing FE)."""
    return df[col] - df.groupby(group_col)[col].transform("mean")


def ssaggregate(y_resid, x_resid, shares_df, shift_col="shift_w"):
    """
    BHJ (2022) ssaggregate procedure.

    1. For each shock k, compute exposure-weighted average of residualized Y and X:
         Y_k = Σ_m (s_{mk} / S_k) × Y~_m
         X_k = Σ_m (s_{mk} / S_k) × X~_m
       where S_k = Σ_m s_{mk} (total exposure to shock k)

    2. Run shock-level regression:
         Y_k = α + β × X_k + ε_k
       with heteroskedasticity-robust SEs (or weighted by S_k)

    Parameters
    ----------
    y_resid : Series — residualized outcome, indexed by (msa_code, year, qtr)
    x_resid : Series — residualized endogenous var, indexed by (msa_code, year, qtr)
    shares_df : DataFrame with columns [msa_code, NAICS3, year, qtr, share, shift_w]

    Returns
    -------
    dict with beta, se, t, p, n_shocks, effective_n
    """
    # Create (msa, period) identifier
    resid_df = pd.DataFrame({
        "y_resid": y_resid.values,
        "x_resid": x_resid.values,
    }, index=y_resid.index)

    # Merge residuals into components
    components = shares_df.copy()
    components["msa_period"] = (
        components["msa_code"] + "_" +
        components["year"].astype(str) + "_" +
        components["qtr"].astype(str)
    )

    # Build matching index for residuals
    resid_df = resid_df.reset_index()
    resid_df["msa_period"] = (
        resid_df["msa_code"] + "_" +
        resid_df["year"].astype(str) + "_" +
        resid_df["qtr"].astype(str)
    )
    resid_map = resid_df.set_index("msa_period")[["y_resid", "x_resid"]]

    components = components.merge(
        resid_map, left_on="msa_period", right_index=True, how="inner"
    )

    # Exposure weights: s_{mk} for each shock k
    # Total exposure to shock k: S_k = Σ_m s_{mk}
    shock_exposure = (
        components.groupby(["NAICS3", "year", "qtr"], as_index=False)["share"]
        .sum()
        .rename(columns={"share": "total_exposure"})
    )

    components = components.merge(
        shock_exposure, on=["NAICS3", "year", "qtr"]
    )

    # Weight: w_{mk} = s_{mk} / S_k
    components["weight"] = components["share"] / components["total_exposure"]

    # Aggregate to shock level
    components["y_weighted"] = components["weight"] * components["y_resid"]
    components["x_weighted"] = components["weight"] * components["x_resid"]

    shock_level = components.groupby(["NAICS3", "year", "qtr"], as_index=False).agg(
        y_shock=("y_weighted", "sum"),
        x_shock=("x_weighted", "sum"),
        total_exposure=("total_exposure", "first"),
        shift=("shift_w", "first"),
        n_msas=("msa_code", "nunique"),
    )

    # Drop shocks with zero exposure
    shock_level = shock_level[shock_level["total_exposure"] > 0].copy()

    # Shock-level regression (weighted by total exposure)
    Y = shock_level["y_shock"].values
    X = sm.add_constant(shock_level["x_shock"].values)
    W = shock_level["total_exposure"].values

    model = sm.WLS(Y, X, weights=W).fit(cov_type="HC1")

    # Effective number of shocks (Herfindahl-based)
    w_normalized = W / W.sum()
    effective_n = 1.0 / (w_normalized ** 2).sum()

    return {
        "beta": model.params[1],
        "se_robust": model.bse[1],
        "t": model.tvalues[1],
        "p": model.pvalues[1],
        "n_shocks": len(shock_level),
        "effective_n": effective_n,
        "r2": model.rsquared,
    }


def main():
    print("=" * 60)
    print("EXPOSURE-ROBUST INFERENCE (BHJ ssaggregate)")
    print("=" * 60)

    # Load data
    print("\n[1] Loading data...")
    components = load_bartik_components()
    bartik = load_bartik_instrument()
    unemp = load_unemployment()

    print(f"  Components: {len(components):,} rows")
    print(f"  Bartik instrument: {len(bartik):,} rows")
    print(f"  Unemployment: {len(unemp):,} rows")

    # Merge unemployment onto bartik
    panel = bartik.merge(unemp, on=["BestFitMSA4", "year", "qtr"], how="inner")
    print(f"  Merged panel: {len(panel):,} obs")

    # ── Step 1: Residualize outcome and endogenous variable ────────────
    print("\n[2] Residualizing (absorbing year FE)...")

    # Absorb year × quarter FE (quarterly data needs year-quarter, not just year)
    panel["year_qtr"] = panel["year"].astype(str) + "_" + panel["qtr"].astype(str)
    panel["unemp_resid"] = demean_by_group(panel, "unemp_quarter", "year_qtr")
    panel["bartik_resid"] = demean_by_group(panel, "bartik", "year_qtr")

    # ── Step 2: Run ssaggregate ───────────────────────────────────────
    print("\n[3] Running ssaggregate (shock-level regression)...")

    # Need to index residuals by (msa_code, year, qtr)
    panel_indexed = panel.set_index(["msa_code", "year", "qtr"])

    result = ssaggregate(
        panel_indexed["unemp_resid"],
        panel_indexed["bartik_resid"],
        components,
    )

    print(f"\n  Shock-level regression results:")
    print(f"    β (bartik → unemp) = {result['beta']:.4f}")
    print(f"    SE (exposure-robust) = {result['se_robust']:.4f}")
    print(f"    t = {result['t']:.2f}")
    print(f"    p = {result['p']:.4f}")
    print(f"    N shocks = {result['n_shocks']}")
    print(f"    Effective N = {result['effective_n']:.1f}")
    print(f"    R² = {result['r2']:.4f}")

    # ── Step 3: Compare with standard MSA-clustered SEs ────────────────
    print("\n[4] Comparison with standard approaches...")

    # Standard MSA-level regression with MSA-clustered SEs
    Y_msa = panel["unemp_resid"].values
    X_msa = sm.add_constant(panel["bartik_resid"].values)

    # MSA-clustered
    model_msa = sm.OLS(Y_msa, X_msa).fit(
        cov_type="cluster",
        cov_kwds={"groups": panel["msa_code"].values}
    )

    # Homoskedastic
    model_homo = sm.OLS(Y_msa, X_msa).fit()

    print(f"\n  SE comparison:")
    print(f"    Homoskedastic SE:     {model_homo.bse[1]:.4f}")
    print(f"    MSA-clustered SE:     {model_msa.bse[1]:.4f}")
    print(f"    Exposure-robust SE:   {result['se_robust']:.4f}")
    print(f"    Ratio (robust/MSA):   {result['se_robust'] / model_msa.bse[1]:.2f}")

    # ── Step 4: Save results ──────────────────────────────────────────
    print("\n[5] Saving results...")

    results_df = pd.DataFrame([
        {
            "method": "Homoskedastic",
            "beta": model_homo.params[1],
            "se": model_homo.bse[1],
            "t": model_homo.tvalues[1],
            "p": model_homo.pvalues[1],
            "n_obs": len(panel),
        },
        {
            "method": "MSA-clustered",
            "beta": model_msa.params[1],
            "se": model_msa.bse[1],
            "t": model_msa.tvalues[1],
            "p": model_msa.pvalues[1],
            "n_obs": len(panel),
        },
        {
            "method": "Exposure-robust (ssaggregate)",
            "beta": result["beta"],
            "se": result["se_robust"],
            "t": result["t"],
            "p": result["p"],
            "n_obs": result["n_shocks"],
            "effective_n": result["effective_n"],
        },
    ])

    out_path = os.path.join(OUT_DIR, "ssaggregate_results.csv")
    results_df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")

    print("\n" + "=" * 80)
    print("SSAGGREGATE SUMMARY")
    print("=" * 80)
    print(f"{'Method':<30} {'β':>10} {'SE':>10} {'t':>8} {'p':>8}")
    print("-" * 70)
    for _, row in results_df.iterrows():
        sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else ""
        print(f"{row['method']:<30} {row['beta']:>10.4f} {row['se']:>10.4f} "
              f"{row['t']:>7.2f} {row['p']:>7.4f}{sig}")
    print("=" * 80)

    if result["se_robust"] > model_msa.bse[1]:
        print("\n⚠ Exposure-robust SEs are LARGER than MSA-clustered SEs.")
        print("  This suggests MSA-clustered SEs may understate uncertainty.")
        print("  Report exposure-robust SEs in the paper for conservative inference.")
    else:
        print("\n✓ Exposure-robust SEs are smaller than MSA-clustered SEs.")
        print("  MSA-clustered SEs are conservative. Both are valid.")


if __name__ == "__main__":
    main()
