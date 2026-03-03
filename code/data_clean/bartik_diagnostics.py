"""
BHJ Diagnostics Suite for Bartik Shift-Share Instrument
=======================================================

Runs the full set of diagnostics recommended by:
  - Borusyak, Hull & Jaravel (2022, 2025)
  - Goldsmith-Pinkham, Sorkin & Swift (2020)

Diagnostics:
  1. Effective number of shocks
  2. Shock-level balance tests
  3. Rotemberg weight decomposition
  4. Coefficient stability (drop top-5 industries)
  5. Placebo pre-trend test
  6. First-stage F-statistic

Input:  data/bartik/bartik_components.parquet
        data/bartik/bartik_instrument.parquet
        data/LAUS/LAUS_msa.csv
Output: data/bartik/diagnostics/  (CSV reports + summary)
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
BARTIK_DIR = os.path.join(DATA_DIR, "bartik")
DIAG_DIR = os.path.join(BARTIK_DIR, "diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────

print("Loading data...")
components = pd.read_parquet(os.path.join(BARTIK_DIR, "bartik_components.parquet"))
bartik = pd.read_parquet(os.path.join(BARTIK_DIR, "bartik_instrument.parquet"))
laus = pd.read_csv(os.path.join(DATA_DIR, "LAUS", "LAUS_msa.csv"), low_memory=False)

# Prepare LAUS: quarterly average unemployment rate
laus["BestFitMSA"] = pd.to_numeric(laus["BestFitMSA"], errors="coerce")
laus["unemploymentRate_msa"] = pd.to_numeric(laus["unemploymentRate_msa"], errors="coerce")
laus["qtr"] = ((laus["Month"] - 1) // 3) + 1
laus_q = (
    laus.dropna(subset=["unemploymentRate_msa"])
    .groupby(["BestFitMSA", "Year", "qtr"], as_index=False)
    .agg(unemp_rate=("unemploymentRate_msa", "mean"))
)
laus_q.rename(columns={"Year": "year"}, inplace=True)
laus_q["BestFitMSA"] = laus_q["BestFitMSA"].astype(int)
# LAUS uses 5-digit CBSA codes (e.g. 13820), Bartik uses 4-digit QCEW codes (1382)
# Mapping: QCEW code * 10 = CBSA code
laus_q["BestFitMSA4"] = laus_q["BestFitMSA"] // 10

# Merge bartik with unemployment
merged = bartik.merge(laus_q, on=["BestFitMSA4", "year", "qtr"], how="inner")
print(f"Merged instrument + unemployment: {len(merged):,} obs")

results = {}

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 1: Effective Number of Shocks
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 1: Effective Number of Shocks")
print("=" * 60)

# Compute importance weights for each industry
# w_k = Σ_m s_{m,k,t0}  (sum of shares across MSAs for each industry)
# Then: effective N = 1 / Σ_k (w_k / Σ_k w_k)^2  = 1 / HHI

# Get baseline shares (unique per MSA × industry)
shares = components[["msa_code", "NAICS3", "share"]].drop_duplicates(
    subset=["msa_code", "NAICS3"]
)

# Industry importance weights
w_k = shares.groupby("NAICS3")["share"].sum().rename("weight")
w_k_normalized = w_k / w_k.sum()
hhi = (w_k_normalized ** 2).sum()
effective_n = 1.0 / hhi

print(f"  Number of industries: {len(w_k)}")
print(f"  HHI of industry weights: {hhi:.4f}")
print(f"  Effective number of shocks: {effective_n:.1f}")
if effective_n < 20:
    print(f"  ⚠️  WARNING: Below threshold of 20. Asymptotic approximations may be poor.")
else:
    print(f"  ✅ PASS: Above threshold of 20.")

results["effective_n_shocks"] = effective_n
results["hhi_industry_weights"] = hhi
results["n_industries"] = len(w_k)

# Top 10 industries by weight
top_industries = w_k_normalized.sort_values(ascending=False).head(10)
print("\n  Top 10 industries by importance weight:")
for naics, wt in top_industries.items():
    print(f"    NAICS {naics}: {wt:.4f} ({wt*100:.1f}%)")

top_industries.to_csv(os.path.join(DIAG_DIR, "top_industries_by_weight.csv"))

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 2: Shock-Level Balance Tests
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 2: Shock-Level Balance Tests")
print("=" * 60)

# Test whether national industry growth rates predict lagged MSA-level outcomes
# Following BHJ: regress shift_{k,t} on exposure-weighted lagged outcomes

# First, compute lagged unemployment at MSA level
merged_sorted = merged.sort_values(["BestFitMSA4", "year", "qtr"])
merged_sorted["unemp_lag1"] = merged_sorted.groupby("BestFitMSA4")["unemp_rate"].shift(1)
merged_sorted["unemp_lag4"] = merged_sorted.groupby("BestFitMSA4")["unemp_rate"].shift(4)

# Merge lagged outcomes into components
comp_bal = components.merge(
    bartik[["msa_code", "year", "qtr", "BestFitMSA4"]],
    on=["msa_code", "year", "qtr"],
    how="inner",
)
comp_bal = comp_bal.merge(
    merged_sorted[["BestFitMSA4", "year", "qtr", "unemp_lag1", "unemp_lag4"]],
    on=["BestFitMSA4", "year", "qtr"],
    how="inner",
)

# Shock-level balance: for each industry × quarter, compute
# exposure-weighted average of lagged outcomes

# Compute weighted values
comp_bal["share_x_ulag1"] = comp_bal["share"] * comp_bal["unemp_lag1"]
comp_bal["share_x_ulag4"] = comp_bal["share"] * comp_bal["unemp_lag4"]

shock_bal = (
    comp_bal.groupby(["NAICS3", "year", "qtr"], as_index=False)
    .agg(
        shift_w=("shift_w", "mean"),
        share_x_ulag1_sum=("share_x_ulag1", "sum"),
        share_x_ulag4_sum=("share_x_ulag4", "sum"),
        share_sum=("share", "sum"),
    )
)
shock_bal["unemp_lag1_wtd"] = shock_bal["share_x_ulag1_sum"] / shock_bal["share_sum"]
shock_bal["unemp_lag4_wtd"] = shock_bal["share_x_ulag4_sum"] / shock_bal["share_sum"]
shock_bal["weight"] = shock_bal["share_sum"]

# Weighted regression: shift ~ lagged_unemp, weighted by industry importance
from numpy.linalg import lstsq

for outcome_col, label in [("unemp_lag1_wtd", "1-quarter lag"), ("unemp_lag4_wtd", "4-quarter lag")]:
    valid = shock_bal.dropna(subset=["shift_w", outcome_col, "weight"])
    if len(valid) < 10:
        print(f"\n  {label}: insufficient observations")
        continue

    y = valid["shift_w"].values
    X = np.column_stack([np.ones(len(valid)), valid[outcome_col].values])
    w = np.sqrt(valid["weight"].values)

    # WLS
    Xw = X * w[:, None]
    yw = y * w
    beta, residuals, _, _ = lstsq(Xw, yw, rcond=None)

    # Standard errors
    resid = yw - Xw @ beta
    n, k = X.shape
    sigma2 = (resid ** 2).sum() / (n - k)
    var_beta = sigma2 * np.linalg.inv(Xw.T @ Xw)
    se = np.sqrt(np.diag(var_beta))
    t_stat = beta[1] / se[1]
    p_val = 2 * (1 - __import__("scipy").stats.t.cdf(abs(t_stat), n - k))

    print(f"\n  Balance test ({label}):")
    print(f"    Coefficient on lagged unemployment: {beta[1]:.6f}")
    print(f"    SE: {se[1]:.6f}, t={t_stat:.3f}, p={p_val:.3f}")
    if p_val < 0.1:
        print(f"    ⚠️  WARNING: p < 0.1. Shocks may predict lagged outcomes.")
    else:
        print(f"    ✅ PASS: No significant prediction of lagged outcomes.")

    results[f"balance_{label}_coef"] = beta[1]
    results[f"balance_{label}_pval"] = p_val

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 3: Rotemberg Weight Decomposition
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 3: Rotemberg Weight Decomposition")
print("=" * 60)

# Rotemberg weights measure which industries drive the 2SLS estimate.
# α_k = (Σ_m s_{mk} * Δx_m) * g_k / (Σ_m z_m * Δx_m)
# where z_m = Bartik instrument, x_m = endogenous variable (unemployment)

# Simplified computation: industry k's contribution to the first stage
# For each industry, compute: sum of (share * instrument * endogenous variable)

# Merge unemployment into components
comp_rot = components.merge(
    bartik[["msa_code", "year", "qtr", "BestFitMSA4"]],
    on=["msa_code", "year", "qtr"],
    how="inner",
)
comp_rot = comp_rot.merge(
    laus_q, on=["BestFitMSA4", "year", "qtr"], how="inner",
)

# Approximate Rotemberg weights
# For each industry k: α_k ∝ Σ_{m,t} s_{mk} * g_{kt} * unemp_{mt}
comp_rot["rot_component"] = comp_rot["share"] * comp_rot["shift_w"] * comp_rot["unemp_rate"]
rot_weights = comp_rot.groupby("NAICS3")["rot_component"].sum()
rot_weights = rot_weights / rot_weights.sum()
rot_weights = rot_weights.sort_values(ascending=False)

print("  Top 10 industries by Rotemberg weight:")
for i, (naics, wt) in enumerate(rot_weights.head(10).items()):
    print(f"    {i+1}. NAICS {naics}: {wt:.4f} ({wt*100:.1f}%)")

top5_cumulative = rot_weights.head(5).sum()
n_negative = (rot_weights < 0).sum()
print(f"\n  Cumulative weight, top 5: {top5_cumulative:.3f}")
print(f"  Number of negative weights: {n_negative}")
print(f"  Sum of negative weights: {rot_weights[rot_weights < 0].sum():.4f}")

if top5_cumulative > 0.5:
    print(f"  ⚠️  NOTE: Top 5 industries account for >{top5_cumulative:.0%} of the estimate.")
else:
    print(f"  ✅ Estimate not dominated by a few industries.")

results["rotemberg_top5_cumulative"] = top5_cumulative
results["rotemberg_n_negative"] = n_negative

rot_weights.to_csv(os.path.join(DIAG_DIR, "rotemberg_weights.csv"))

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 4: Coefficient Stability (Drop Top-5 Industries)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 4: Coefficient Stability")
print("=" * 60)

# Re-estimate the first stage dropping top Rotemberg-weight industries one at a time
top5_industries = rot_weights.head(5).index.tolist()

# Baseline first stage: regress unemp on bartik
from scipy.stats import pearsonr

base_corr, base_p = pearsonr(merged["bartik"], merged["unemp_rate"])
print(f"  Baseline correlation (bartik, unemp): {base_corr:.4f} (p={base_p:.2e})")

print("\n  Dropping top Rotemberg industries one at a time:")
for drop_naics in top5_industries:
    # Recompute instrument excluding this industry
    comp_drop = components[components["NAICS3"] != drop_naics]
    bartik_drop = (
        comp_drop.groupby(["msa_code", "year", "qtr"], as_index=False)["component"]
        .sum()
        .rename(columns={"component": "bartik_drop"})
    )
    # Standardize within year
    bartik_drop["bartik_drop"] = bartik_drop.groupby("year")["bartik_drop"].transform(
        lambda x: (x - x.mean()) / x.std()
    )
    # Merge with unemployment
    bartik_drop = bartik_drop.merge(
        bartik[["msa_code", "year", "qtr", "BestFitMSA4"]],
        on=["msa_code", "year", "qtr"],
        how="inner",
    )
    merged_drop = bartik_drop.merge(laus_q, on=["BestFitMSA4", "year", "qtr"], how="inner")
    corr_drop, p_drop = pearsonr(merged_drop["bartik_drop"], merged_drop["unemp_rate"])
    pct_change = (corr_drop - base_corr) / abs(base_corr) * 100
    print(f"    Drop NAICS {drop_naics}: corr={corr_drop:.4f} "
          f"(change: {pct_change:+.1f}%)")

results["baseline_corr_bartik_unemp"] = base_corr

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 5: Placebo Pre-Trend Test
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 5: Placebo Pre-Trend Test")
print("=" * 60)

# Does the instrument predict pre-period unemployment levels?
# Regress bartik_{m,t} on unemp_{m,t-4} (1-year lag)

placebo = merged_sorted.dropna(subset=["bartik", "unemp_lag4"])
corr_placebo, p_placebo = pearsonr(placebo["bartik"], placebo["unemp_lag4"])
print(f"  Correlation (bartik_t, unemp_{'{t-4}'}): {corr_placebo:.4f} (p={p_placebo:.2e})")

if abs(p_placebo) < 0.05:
    print(f"  ⚠️  WARNING: Instrument significantly predicts lagged outcomes.")
else:
    print(f"  ✅ PASS: No significant predictive power for pre-period outcomes.")

results["placebo_pretrend_corr"] = corr_placebo
results["placebo_pretrend_pval"] = p_placebo

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC 6: First-Stage F-Statistic
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC 6: First-Stage F-Statistic")
print("=" * 60)

# Simple first stage: unemp ~ bartik (+ year FE)
from scipy.stats import f as f_dist

# Year-demeaned
merged_dm = merged.copy()
for col in ["bartik", "unemp_rate"]:
    merged_dm[col] = merged_dm.groupby("year")[col].transform(
        lambda x: x - x.mean()
    )

valid = merged_dm.dropna(subset=["bartik", "unemp_rate"])
y = valid["unemp_rate"].values
x = valid["bartik"].values
X = np.column_stack([np.ones(len(valid)), x])

beta, _, _, _ = lstsq(X, y, rcond=None)
resid = y - X @ beta
n, k = X.shape
rss = (resid ** 2).sum()
tss = ((y - y.mean()) ** 2).sum()
r2 = 1 - rss / tss

# F-stat for the single instrument
f_stat = (tss - rss) / (k - 1) / (rss / (n - k))

print(f"  Simple first stage (year-demeaned):")
print(f"    Coefficient: {beta[1]:.4f}")
print(f"    R²: {r2:.4f}")
print(f"    F-statistic: {f_stat:.1f}")
print(f"    N: {n:,}")

if f_stat < 10:
    print(f"  ⚠️  WARNING: F < 10. Weak instrument concern.")
elif f_stat < 25:
    print(f"  ⚠️  NOTE: F between 10-25. Adequate but not strong.")
else:
    print(f"  ✅ PASS: F > 25. Strong instrument.")

results["first_stage_F"] = f_stat
results["first_stage_coef"] = beta[1]
results["first_stage_r2"] = r2
results["first_stage_n"] = n

# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)

summary_rows = [
    ("Effective # of shocks", f"{results['effective_n_shocks']:.1f}",
     "PASS" if results["effective_n_shocks"] >= 20 else "WARN"),
    ("First-stage F", f"{results['first_stage_F']:.1f}",
     "PASS" if results["first_stage_F"] >= 25 else ("MARGINAL" if results["first_stage_F"] >= 10 else "WARN")),
    ("Balance (1-qtr lag)", f"p={results.get('balance_1-quarter lag_pval', 'N/A'):.3f}" if isinstance(results.get('balance_1-quarter lag_pval'), float) else "N/A",
     "PASS" if results.get("balance_1-quarter lag_pval", 1) >= 0.1 else "WARN"),
    ("Balance (4-qtr lag)", f"p={results.get('balance_4-quarter lag_pval', 'N/A'):.3f}" if isinstance(results.get('balance_4-quarter lag_pval'), float) else "N/A",
     "PASS" if results.get("balance_4-quarter lag_pval", 1) >= 0.1 else "WARN"),
    ("Rotemberg top-5 share", f"{results['rotemberg_top5_cumulative']:.3f}",
     "NOTE" if results["rotemberg_top5_cumulative"] > 0.5 else "PASS"),
    ("Negative Rotemberg weights", f"{results['rotemberg_n_negative']}",
     "PASS" if results["rotemberg_n_negative"] <= 5 else "NOTE"),
    ("Placebo pre-trend", f"p={results['placebo_pretrend_pval']:.3f}",
     "PASS" if results["placebo_pretrend_pval"] >= 0.05 else "WARN"),
]

print(f"\n  {'Diagnostic':<30} {'Value':<20} {'Status'}")
print(f"  {'-'*30} {'-'*20} {'-'*8}")
for label, value, status in summary_rows:
    flag = "✅" if status == "PASS" else ("⚠️ " if status == "WARN" else "📝")
    print(f"  {label:<30} {value:<20} {flag} {status}")

# Save results
results_df = pd.DataFrame([results])
results_df.to_csv(os.path.join(DIAG_DIR, "diagnostic_summary.csv"), index=False)
print(f"\n  Results saved to {DIAG_DIR}/")
