"""
Bartik IV Diagnostic Fixes — JRS Dynamic Controls + Robustness Variants
========================================================================

Addresses the balance test failures from baseline diagnostics by implementing:

  1. JRS Dynamic Control (Jaeger, Ruist & Stuhler 2018):
     Include bartik_{t-4} as a control in the first stage to absorb serial
     correlation in shocks. Tests conditional exogeneity net of lagged shocks.

  2. No-NAICS-611 Variant:
     NAICS 611 (Education) has ρ=0.94 annual autocorrelation and carries ~31%
     Rotemberg weight. Re-run diagnostics excluding it.

  3. Change Specification:
     Instrument unemployment CHANGES (Δunemp) instead of LEVELS, since the
     Bartik instrument captures employment shocks (flow) not labor market state
     (stock). Correlates r=-0.27 with changes vs r=-0.04 with levels.

  4. Combined Recommendation:
     Primary spec: JRS control + change specification
     Robustness: No-611 variant

Input:  data/bartik/bartik_instrument.parquet (with bartik_no611, bartik_lag4)
        data/bartik/bartik_components.parquet
        data/LAUS/LAUS_msa.csv
Output: data/bartik/diagnostics/fix_results.csv
        data/bartik/diagnostics/fix_summary.txt
"""

import pandas as pd
import numpy as np
import os
import warnings
from numpy.linalg import lstsq
from scipy import stats

warnings.filterwarnings("ignore")

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
BARTIK_DIR = os.path.join(DATA_DIR, "bartik")
DIAG_DIR = os.path.join(BARTIK_DIR, "diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)


def first_stage_f(y, X):
    """Compute F-statistic for the first variable in X (after constant)."""
    beta, _, _, _ = lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    rss = (resid ** 2).sum()
    tss = ((y - y.mean()) ** 2).sum()
    r2 = 1 - rss / tss
    f_stat = ((tss - rss) / (k - 1)) / (rss / (n - k))
    return f_stat, beta[1], r2, n


def partial_f(y, X_full, X_restricted):
    """Compute partial F-stat: how much does the excluded variable(s) add?"""
    beta_full, _, _, _ = lstsq(X_full, y, rcond=None)
    beta_rest, _, _, _ = lstsq(X_restricted, y, rcond=None)
    rss_full = ((y - X_full @ beta_full) ** 2).sum()
    rss_rest = ((y - X_restricted @ beta_rest) ** 2).sum()
    n = len(y)
    k_full = X_full.shape[1]
    k_rest = X_restricted.shape[1]
    q = k_full - k_rest
    f_stat = ((rss_rest - rss_full) / q) / (rss_full / (n - k_full))
    return f_stat


def balance_test(shift_vals, lagged_outcome_vals, weights):
    """Weighted regression of shifts on lagged outcomes. Returns coef, p-value."""
    valid = ~(np.isnan(shift_vals) | np.isnan(lagged_outcome_vals) | np.isnan(weights))
    y = shift_vals[valid]
    x = lagged_outcome_vals[valid]
    w = np.sqrt(weights[valid])
    X = np.column_stack([np.ones(len(y)), x])
    Xw = X * w[:, None]
    yw = y * w
    beta, _, _, _ = lstsq(Xw, yw, rcond=None)
    resid = yw - Xw @ beta
    n, k = X.shape
    sigma2 = (resid ** 2).sum() / (n - k)
    var_beta = sigma2 * np.linalg.inv(Xw.T @ Xw)
    se = np.sqrt(np.diag(var_beta))
    t_stat = beta[1] / se[1]
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - k))
    r2 = 1 - (resid ** 2).sum() / ((yw - yw.mean()) ** 2).sum()
    return beta[1], se[1], t_stat, p_val, r2, n


# ── Load data ──────────────────────────────────────────────────────────
print("Loading data...")
components = pd.read_parquet(os.path.join(BARTIK_DIR, "bartik_components.parquet"))
bartik = pd.read_parquet(os.path.join(BARTIK_DIR, "bartik_instrument.parquet"))
laus = pd.read_csv(os.path.join(DATA_DIR, "LAUS", "LAUS_msa.csv"), low_memory=False)

# Prepare LAUS
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
laus_q["BestFitMSA4"] = laus_q["BestFitMSA"] // 10

# Merge
merged = bartik.merge(laus_q, on=["BestFitMSA4", "year", "qtr"], how="inner")
merged = merged.sort_values(["BestFitMSA4", "year", "qtr"]).reset_index(drop=True)

# Compute unemployment changes (4-quarter diff)
merged["unemp_change4"] = merged.groupby("BestFitMSA4")["unemp_rate"].diff(4)
# Also 1-quarter change
merged["unemp_change1"] = merged.groupby("BestFitMSA4")["unemp_rate"].diff(1)
# Lagged unemployment for balance tests
merged["unemp_lag1"] = merged.groupby("BestFitMSA4")["unemp_rate"].shift(1)
merged["unemp_lag4"] = merged.groupby("BestFitMSA4")["unemp_rate"].shift(4)

print(f"Merged: {len(merged):,} obs, {merged['BestFitMSA4'].nunique()} MSAs")

results = {}

# ══════════════════════════════════════════════════════════════════════
# SPEC 0: Baseline (for comparison)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 0: BASELINE — bartik → unemp_level (year-demeaned)")
print("=" * 60)

valid = merged.dropna(subset=["bartik", "unemp_rate"]).copy()
for col in ["bartik", "unemp_rate"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_rate"].values
X = np.column_stack([np.ones(len(y)), valid["bartik"].values])
f, coef, r2, n = first_stage_f(y, X)
print(f"  F = {f:.1f}, coef = {coef:.4f}, R² = {r2:.4f}, N = {n:,}")
results["spec0_F"] = f
results["spec0_coef"] = coef

# ══════════════════════════════════════════════════════════════════════
# SPEC 1: Change specification — bartik → Δunemp (4-quarter change)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 1: CHANGE SPEC — bartik → Δ4_unemp (year-demeaned)")
print("=" * 60)

valid = merged.dropna(subset=["bartik", "unemp_change4"]).copy()
for col in ["bartik", "unemp_change4"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_change4"].values
X = np.column_stack([np.ones(len(y)), valid["bartik"].values])
f, coef, r2, n = first_stage_f(y, X)
print(f"  F = {f:.1f}, coef = {coef:.4f}, R² = {r2:.4f}, N = {n:,}")
results["spec1_F"] = f
results["spec1_coef"] = coef

# Balance test for change spec
corr, p = stats.pearsonr(
    merged.dropna(subset=["bartik", "unemp_lag4"])["bartik"],
    merged.dropna(subset=["bartik", "unemp_lag4"])["unemp_lag4"],
)
print(f"  Balance (corr with unemp_lag4): r = {corr:.4f}, p = {p:.3e}")
results["spec1_balance_r"] = corr
results["spec1_balance_p"] = p

# ══════════════════════════════════════════════════════════════════════
# SPEC 2: JRS Dynamic — bartik + bartik_lag4 → unemp_level
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 2: JRS DYNAMIC — bartik + bartik_lag4 → unemp (year-demeaned)")
print("=" * 60)

valid = merged.dropna(subset=["bartik", "bartik_lag4", "unemp_rate"]).copy()
for col in ["bartik", "bartik_lag4", "unemp_rate"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_rate"].values
X_full = np.column_stack([np.ones(len(y)), valid["bartik"].values, valid["bartik_lag4"].values])
X_restricted = np.column_stack([np.ones(len(y)), valid["bartik_lag4"].values])

# Full model F
f, coef, r2, n = first_stage_f(y, X_full)
# Partial F for bartik (controlling for lag)
pf = partial_f(y, X_full, X_restricted)
print(f"  Full model F = {f:.1f}, N = {n:,}")
print(f"  Partial F (bartik | bartik_lag4) = {pf:.1f}")

beta_full, _, _, _ = lstsq(X_full, y, rcond=None)
print(f"  Coefficients: bartik = {beta_full[1]:.4f}, bartik_lag4 = {beta_full[2]:.4f}")
results["spec2_partialF"] = pf
results["spec2_coef_current"] = beta_full[1]
results["spec2_coef_lag4"] = beta_full[2]

# ══════════════════════════════════════════════════════════════════════
# SPEC 3: JRS Dynamic + Change — bartik + bartik_lag4 → Δ4_unemp
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 3: JRS + CHANGE — bartik + bartik_lag4 → Δ4_unemp (year-demeaned)")
print("=" * 60)

valid = merged.dropna(subset=["bartik", "bartik_lag4", "unemp_change4"]).copy()
for col in ["bartik", "bartik_lag4", "unemp_change4"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_change4"].values
X_full = np.column_stack([np.ones(len(y)), valid["bartik"].values, valid["bartik_lag4"].values])
X_restricted = np.column_stack([np.ones(len(y)), valid["bartik_lag4"].values])

f, coef, r2, n = first_stage_f(y, X_full)
pf = partial_f(y, X_full, X_restricted)
print(f"  Full model F = {f:.1f}, N = {n:,}")
print(f"  Partial F (bartik | bartik_lag4) = {pf:.1f}")

beta_full, _, _, _ = lstsq(X_full, y, rcond=None)
print(f"  Coefficients: bartik = {beta_full[1]:.4f}, bartik_lag4 = {beta_full[2]:.4f}")
results["spec3_partialF"] = pf
results["spec3_coef_current"] = beta_full[1]
results["spec3_coef_lag4"] = beta_full[2]

# ══════════════════════════════════════════════════════════════════════
# SPEC 4: No-611 Variant — bartik_no611 → unemp_level
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 4: NO-611 — bartik_no611 → unemp (year-demeaned)")
print("=" * 60)

valid = merged.dropna(subset=["bartik_no611", "unemp_rate"]).copy()
for col in ["bartik_no611", "unemp_rate"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_rate"].values
X = np.column_stack([np.ones(len(y)), valid["bartik_no611"].values])
f, coef, r2, n = first_stage_f(y, X)
print(f"  F = {f:.1f}, coef = {coef:.4f}, R² = {r2:.4f}, N = {n:,}")
results["spec4_F"] = f
results["spec4_coef"] = coef

# No-611 balance test
corr_no611, p_no611 = stats.pearsonr(
    merged.dropna(subset=["bartik_no611", "unemp_lag4"])["bartik_no611"],
    merged.dropna(subset=["bartik_no611", "unemp_lag4"])["unemp_lag4"],
)
print(f"  Balance (corr with unemp_lag4): r = {corr_no611:.4f}, p = {p_no611:.3e}")
results["spec4_balance_r"] = corr_no611
results["spec4_balance_p"] = p_no611

# No-611 effective number of shocks
shares = components[components["NAICS3"] != "611"][["msa_code", "NAICS3", "share"]].drop_duplicates(
    subset=["msa_code", "NAICS3"]
)
w_k = shares.groupby("NAICS3")["share"].sum()
w_k_norm = w_k / w_k.sum()
eff_n_no611 = 1.0 / (w_k_norm ** 2).sum()
print(f"  Effective N of shocks (no-611): {eff_n_no611:.1f}")
results["spec4_effective_n"] = eff_n_no611

# ══════════════════════════════════════════════════════════════════════
# SPEC 5: No-611 + JRS — bartik_no611 + lag → unemp_level
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SPEC 5: NO-611 + JRS — bartik_no611 + bartik_no611_lag4 → unemp")
print("=" * 60)

# Compute lag for no611 variant
merged_sorted = merged.sort_values(["BestFitMSA4", "year", "qtr"]).copy()
merged_sorted["bartik_no611_lag4"] = merged_sorted.groupby("BestFitMSA4")["bartik_no611"].shift(4)

valid = merged_sorted.dropna(subset=["bartik_no611", "bartik_no611_lag4", "unemp_rate"]).copy()
for col in ["bartik_no611", "bartik_no611_lag4", "unemp_rate"]:
    valid[col] = valid.groupby("year")[col].transform(lambda x: x - x.mean())
y = valid["unemp_rate"].values
X_full = np.column_stack([np.ones(len(y)), valid["bartik_no611"].values, valid["bartik_no611_lag4"].values])
X_restricted = np.column_stack([np.ones(len(y)), valid["bartik_no611_lag4"].values])

f, coef, r2, n = first_stage_f(y, X_full)
pf = partial_f(y, X_full, X_restricted)
print(f"  Full model F = {f:.1f}, N = {n:,}")
print(f"  Partial F (bartik_no611 | lag) = {pf:.1f}")
results["spec5_partialF"] = pf

# ══════════════════════════════════════════════════════════════════════
# SHOCK-LEVEL BALANCE TEST — with JRS controls
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SHOCK-LEVEL BALANCE: After JRS Residualization")
print("=" * 60)

# Residualize shifts on lagged shifts to address serial correlation
# Then test whether residualized shifts predict lagged outcomes
comp_bal = components.merge(
    bartik[["msa_code", "year", "qtr", "BestFitMSA4"]],
    on=["msa_code", "year", "qtr"],
    how="inner",
)
comp_bal = comp_bal.merge(
    merged[["BestFitMSA4", "year", "qtr", "unemp_lag1", "unemp_lag4"]],
    on=["BestFitMSA4", "year", "qtr"],
    how="inner",
)

# Compute lagged shifts (4-quarter) for each industry
comp_bal = comp_bal.sort_values(["msa_code", "NAICS3", "year", "qtr"])
comp_bal["shift_w_lag4"] = comp_bal.groupby(["msa_code", "NAICS3"])["shift_w"].shift(4)

# Residualize shift on lagged shift (within each industry)
comp_bal["shift_resid"] = np.nan
for naics, grp in comp_bal.groupby("NAICS3"):
    valid_mask = grp["shift_w"].notna() & grp["shift_w_lag4"].notna()
    if valid_mask.sum() < 10:
        continue
    y_grp = grp.loc[valid_mask, "shift_w"].values
    x_grp = grp.loc[valid_mask, "shift_w_lag4"].values
    X_grp = np.column_stack([np.ones(len(y_grp)), x_grp])
    b, _, _, _ = lstsq(X_grp, y_grp, rcond=None)
    resid_grp = y_grp - X_grp @ b
    comp_bal.loc[grp.index[valid_mask], "shift_resid"] = resid_grp

# Now run balance test on residualized shifts
comp_bal["share_x_ulag4"] = comp_bal["share"] * comp_bal["unemp_lag4"]
shock_bal = (
    comp_bal.dropna(subset=["shift_resid"])
    .groupby(["NAICS3", "year", "qtr"], as_index=False)
    .agg(
        shift_resid=("shift_resid", "mean"),
        share_x_ulag4_sum=("share_x_ulag4", "sum"),
        share_sum=("share", "sum"),
    )
)
shock_bal["unemp_lag4_wtd"] = shock_bal["share_x_ulag4_sum"] / shock_bal["share_sum"]

valid_sb = shock_bal.dropna(subset=["shift_resid", "unemp_lag4_wtd", "share_sum"])
if len(valid_sb) >= 10:
    coef, se, t, p, r2, n = balance_test(
        valid_sb["shift_resid"].values,
        valid_sb["unemp_lag4_wtd"].values,
        valid_sb["share_sum"].values,
    )
    print(f"  Residualized shift ~ lagged unemp (4q):")
    print(f"    coef = {coef:.6f}, SE = {se:.6f}, t = {t:.3f}, p = {p:.3f}")
    print(f"    R² = {r2:.6f}, N = {n:,}")
    if p < 0.1:
        print(f"    ⚠️  Still significant at 10% after JRS residualization")
    else:
        print(f"    ✅ PASS: Not significant after JRS residualization")
    results["jrs_balance_coef"] = coef
    results["jrs_balance_p"] = p


# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY OF FIX SPECIFICATIONS")
print("=" * 60)

specs = [
    ("Spec 0: Baseline (levels)", results.get("spec0_F", np.nan), "—", "—"),
    ("Spec 1: Change (Δ4_unemp)", results.get("spec1_F", np.nan),
     f"r={results.get('spec1_balance_r', np.nan):.4f}",
     f"p={results.get('spec1_balance_p', np.nan):.3f}"),
    ("Spec 2: JRS dynamic (levels)", f"partial={results.get('spec2_partialF', np.nan):.1f}", "—", "—"),
    ("Spec 3: JRS + Change", f"partial={results.get('spec3_partialF', np.nan):.1f}", "—", "—"),
    ("Spec 4: No-611 (levels)", results.get("spec4_F", np.nan),
     f"r={results.get('spec4_balance_r', np.nan):.4f}",
     f"p={results.get('spec4_balance_p', np.nan):.3f}"),
    ("Spec 5: No-611 + JRS", f"partial={results.get('spec5_partialF', np.nan):.1f}", "—", "—"),
]

print(f"\n  {'Specification':<35} {'F-stat':<15} {'Balance':<20} {'p-value'}")
print(f"  {'-'*35} {'-'*15} {'-'*20} {'-'*10}")
for label, f_val, bal, p in specs:
    f_str = f"{f_val:.1f}" if isinstance(f_val, (int, float)) else str(f_val)
    print(f"  {label:<35} {f_str:<15} {bal:<20} {p}")

# ══════════════════════════════════════════════════════════════════════
# RECOMMENDATION
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("RECOMMENDATION FOR IV REGRESSIONS")
print("=" * 60)

recommendation = """
  RECOMMENDED APPROACH for the R regression scripts:

  1. PRIMARY SPECIFICATION (Table):
     - First stage: unemp_rate ~ bartik + bartik_lag4 + FE
       (JRS dynamic control addresses serial correlation concern)
     - Second stage: log_sal ~ purpose × unemp_hat + controls | FE
     - Report partial F-stat on bartik (net of bartik_lag4)

  2. ROBUSTNESS CHECKS (Appendix):
     a) Exclude NAICS 611 (Education): Re-estimate with bartik_no611
     b) Change specification: Instrument Δ4_unemp instead of unemp_level
     c) Both combined: bartik_no611 → Δ4_unemp

  3. REPORTING:
     - Document balance test results AND the JRS justification
     - Note that unemployment persistence makes some balance failure expected
     - Show Rotemberg weights (NAICS 611 dominance) + no-611 robustness
     - Report effective N of shocks (~20-22)

  4. IMPLEMENTATION IN R:
     library(lfe)
     # Primary spec with JRS control:
     felm(log_sal ~ purpose*I(unemp_hat) + controls | FE | (unemp_rate ~ bartik + bartik_lag4) | cluster)
     # Or use ivreg with bartik_lag4 as included exogenous control
"""
print(recommendation)

# Save results
results_df = pd.DataFrame([results])
results_df.to_csv(os.path.join(DIAG_DIR, "fix_results.csv"), index=False)

with open(os.path.join(DIAG_DIR, "fix_summary.txt"), "w") as f:
    f.write("Bartik IV Diagnostic Fix Summary\n")
    f.write("=" * 60 + "\n\n")
    for key, val in sorted(results.items()):
        f.write(f"  {key}: {val}\n")
    f.write("\n" + recommendation)

print(f"\n  Results saved to {DIAG_DIR}/")
print("  DONE")
