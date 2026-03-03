"""
Covariate Balance Tests for Bartik Instrument (Bai 2025-style)
================================================================

Tests whether the Bartik instrument predicts MSA-level observable
characteristics, following Bai (2025) approach: balance on demographics
(not lagged outcomes).

If the instrument is exogenous conditional on FE, it should not predict:
  - Population growth
  - Demographic composition (race shares)
  - Population level (in changes)

These are MSA-level panel regressions:
    X_{m,t} = α + β × Bartik_{m,t} + γ_t + ε_{m,t}

Under exogeneity, β should be near zero / insignificant.
"""

import pandas as pd
import numpy as np
import os
import statsmodels.api as sm

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
OUT_DIR = os.path.join(DATA_DIR, "bartik", "diagnostics")
os.makedirs(OUT_DIR, exist_ok=True)


def load_bartik():
    """Load the Bartik instrument at MSA × quarter level."""
    path = os.path.join(DATA_DIR, "bartik", "bartik_instrument.parquet")
    df = pd.read_parquet(path, engine="fastparquet")
    # Use 4-digit MSA code for merging
    return df[["BestFitMSA4", "year", "qtr", "bartik", "bartik_no611", "bartik_lag4"]]


def load_demographics():
    """Load MSA-level demographic composition (annual)."""
    path = os.path.join(DATA_DIR, "Demographic_Composition", "dem_msa.csv")
    df = pd.read_csv(path)
    # Columns: pop_msa, white_msa, black_msa, americanIndianAlaskaNative_msa,
    #          asian_msa, nativeHawaiianPacificIslander_msa, someOtherRace_msa,
    #          Year, BestFitMSA
    df = df.rename(columns={"Year": "year"})
    return df


def load_population():
    """Load MSA-level population estimates (Census)."""
    frames = []

    # 2010-2019 from cbsa-est2020-alldata.csv
    path1 = os.path.join(DATA_DIR, "Population", "cbsa-est2020-alldata.csv")
    pop1 = pd.read_csv(path1, dtype={"CBSA": str}, encoding="latin1")
    # Keep only CBSA-level rows (no county-level, i.e., STCOU is blank or NaN)
    pop1 = pop1[pop1["STCOU"].isna() | (pop1["STCOU"] == "")].copy()
    if pop1.empty:
        # Alternate: LSAD = "Metropolitan Statistical Area" or "Micropolitan Statistical Area"
        pop1 = pd.read_csv(path1, dtype={"CBSA": str}, encoding="latin1")
        pop1 = pop1[pop1["LSAD"].str.contains("Metropolitan|Micropolitan", na=False)]

    pop_cols = [c for c in pop1.columns if c.startswith("POPESTIMATE")]
    for col in pop_cols:
        yr = int(col.replace("POPESTIMATE", ""))
        tmp = pop1[["CBSA", col]].copy()
        tmp.columns = ["CBSA", "pop"]
        tmp["year"] = yr
        frames.append(tmp)

    # 2020-2022 from cbsa-est2022.csv
    path2 = os.path.join(DATA_DIR, "Population", "cbsa-est2022.csv")
    if os.path.exists(path2):
        pop2 = pd.read_csv(path2, dtype={"CBSA": str}, encoding="latin1")
        pop_cols2 = [c for c in pop2.columns if c.startswith("POPESTIMATE")]
        for col in pop_cols2:
            yr = int(col.replace("POPESTIMATE", ""))
            tmp = pop2[["CBSA", col]].copy()
            tmp.columns = ["CBSA", "pop"]
            tmp["year"] = yr
            frames.append(tmp)

    if not frames:
        return pd.DataFrame()

    pop = pd.concat(frames, ignore_index=True)
    pop["CBSA"] = pop["CBSA"].astype(str).str.strip()
    # Convert 5-digit CBSA to 4-digit QCEW code
    pop["BestFitMSA4"] = pd.to_numeric(pop["CBSA"], errors="coerce") // 10
    pop = pop.dropna(subset=["BestFitMSA4", "pop"])
    pop["BestFitMSA4"] = pop["BestFitMSA4"].astype(int)
    pop["pop"] = pd.to_numeric(pop["pop"], errors="coerce")
    pop = pop[["BestFitMSA4", "year", "pop"]].drop_duplicates()

    # Compute population growth
    pop = pop.sort_values(["BestFitMSA4", "year"])
    pop["pop_lag"] = pop.groupby("BestFitMSA4")["pop"].shift(1)
    pop["pop_growth"] = (pop["pop"] / pop["pop_lag"]) - 1
    pop["log_pop"] = np.log(pop["pop"])

    return pop


def load_laus():
    """Load MSA-level LAUS data (monthly → annual average)."""
    path = os.path.join(DATA_DIR, "LAUS", "LAUS_msa.csv")
    df = pd.read_csv(path)
    # Columns: FIPSState, BestFitMSA, BestFitMSAName_msa, Year, Month,
    #          laborForce_msa, employment_msa, unemployment_msa, unemploymentRate_msa
    df = df.rename(columns={"Year": "year"})
    df["unemploymentRate_msa"] = pd.to_numeric(df["unemploymentRate_msa"], errors="coerce")
    df["laborForce_msa"] = pd.to_numeric(df["laborForce_msa"], errors="coerce")

    # Annual average
    annual = df.groupby(["BestFitMSA", "year"], as_index=False).agg(
        unemp_rate=("unemploymentRate_msa", "mean"),
        labor_force=("laborForce_msa", "mean"),
    )
    # LAUS BestFitMSA is 5-digit CBSA; Bartik BestFitMSA4 is 4-digit QCEW
    annual["BestFitMSA4"] = annual["BestFitMSA"] // 10
    annual = annual.drop(columns=["BestFitMSA"])

    # Labor force participation change
    annual = annual.sort_values(["BestFitMSA4", "year"])
    annual["lf_lag"] = annual.groupby("BestFitMSA4")["labor_force"].shift(1)
    annual["lf_growth"] = (annual["labor_force"] / annual["lf_lag"]) - 1

    return annual


def run_balance_test(df, outcome_var, bartik_var="bartik", year_fe=True,
                     msa_fe=False, label=""):
    """
    Run MSA-level balance test:
        outcome = α + β × bartik + γ_t [+ δ_m] + ε
    Clustered by MSA.

    With msa_fe=True, tests whether bartik predicts within-MSA *changes* in outcome.
    """
    data = df.dropna(subset=[outcome_var, bartik_var])
    if len(data) < 50:
        return None

    y = data[outcome_var].values
    X = data[[bartik_var]].values

    if year_fe:
        year_dummies = pd.get_dummies(data["year"], prefix="yr", drop_first=True).values
        X = np.column_stack([X, year_dummies])

    if msa_fe:
        msa_dummies = pd.get_dummies(data["BestFitMSA4"], prefix="msa", drop_first=True).values
        X = np.column_stack([X, msa_dummies])

    X = sm.add_constant(X)

    try:
        model = sm.OLS(y, X).fit(cov_type="cluster",
                                  cov_kwds={"groups": data["BestFitMSA4"].values})
    except Exception as e:
        print(f"  WARNING: {label} failed: {e}")
        return None

    return {
        "outcome": label,
        "bartik_var": bartik_var,
        "coef": model.params[1],
        "se": model.bse[1],
        "t": model.tvalues[1],
        "p": model.pvalues[1],
        "n": len(data),
        "r2": model.rsquared,
    }


def main():
    print("=" * 60)
    print("COVARIATE BALANCE TESTS (Bai 2025-style)")
    print("=" * 60)

    # Load data
    print("\n[1] Loading data...")
    bartik = load_bartik()
    demographics = load_demographics()
    population = load_population()
    laus = load_laus()

    # Collapse bartik to annual level (average across quarters)
    bartik_annual = bartik.groupby(["BestFitMSA4", "year"], as_index=False).agg(
        bartik=("bartik", "mean"),
        bartik_no611=("bartik_no611", "mean"),
    )

    print(f"  Bartik: {len(bartik_annual)} MSA × year obs")
    print(f"  Demographics: {len(demographics)} rows")
    print(f"  Population: {len(population)} rows")
    print(f"  LAUS: {len(laus)} rows")

    # ── Merge datasets ──────────────────────────────────────────────────
    print("\n[2] Merging datasets...")

    # Demographics merge (demographics uses 5-digit CBSA; Bartik uses 4-digit QCEW)
    dem_merge = demographics.copy()
    dem_merge["BestFitMSA4"] = dem_merge["BestFitMSA"] // 10
    dem_merge = dem_merge.drop(columns=["BestFitMSA"])
    panel = bartik_annual.merge(dem_merge, on=["BestFitMSA4", "year"], how="left")

    # Population merge
    if not population.empty:
        panel = panel.merge(
            population[["BestFitMSA4", "year", "pop", "pop_growth", "log_pop"]],
            on=["BestFitMSA4", "year"], how="left"
        )

    # LAUS merge
    panel = panel.merge(
        laus[["BestFitMSA4", "year", "labor_force", "lf_growth"]],
        on=["BestFitMSA4", "year"], how="left"
    )

    print(f"  Merged panel: {len(panel)} obs, {panel['BestFitMSA4'].nunique()} MSAs")

    # ── Run balance tests ───────────────────────────────────────────────
    print("\n[3] Running balance tests...")

    outcomes = {
        "pop_growth": "Population growth",
        "lf_growth": "Labor force growth",
        "white_msa": "% White",
        "black_msa": "% Black",
        "asian_msa": "% Asian",
        "pop_msa": "Population level",
    }

    results = []
    for var, label in outcomes.items():
        if var not in panel.columns:
            print(f"  Skipping {label} (not in data)")
            continue

        # Primary bartik
        res = run_balance_test(panel, var, "bartik", year_fe=True, label=label)
        if res:
            results.append(res)
            sig = "***" if res["p"] < 0.001 else "**" if res["p"] < 0.01 else "*" if res["p"] < 0.05 else ""
            print(f"  {label:25s}: β={res['coef']:>9.4f}  se={res['se']:>8.4f}  "
                  f"p={res['p']:.3f}{sig}  n={res['n']}")

        # No-611 variant
        res611 = run_balance_test(panel, var, "bartik_no611", year_fe=True,
                                   label=f"{label} (no-611)")
        if res611:
            results.append(res611)

    # ── Balance tests WITH MSA FE (within-MSA variation only) ──────────
    print("\n[3b] Running balance tests with MSA FE (within-MSA changes)...")

    for var, label in outcomes.items():
        if var not in panel.columns:
            continue

        res_msa = run_balance_test(panel, var, "bartik", year_fe=True,
                                    msa_fe=True, label=f"{label} (+ MSA FE)")
        if res_msa:
            results.append(res_msa)
            sig = "***" if res_msa["p"] < 0.001 else "**" if res_msa["p"] < 0.01 else "*" if res_msa["p"] < 0.05 else ""
            print(f"  {label + ' (+ MSA FE)':25s}: β={res_msa['coef']:>9.4f}  se={res_msa['se']:>8.4f}  "
                  f"p={res_msa['p']:.3f}{sig}  n={res_msa['n']}")

    # ── Joint significance: Bonferroni-corrected test across demographics ──
    print("\n[4] Joint significance test (Bonferroni-corrected)...")

    dem_vars = [v for v in ["white_msa", "black_msa", "asian_msa"] if v in panel.columns]
    panel_joint = panel.dropna(subset=dem_vars + ["bartik"])

    if len(panel_joint) > 100:
        n_outcomes = len(dem_vars)
        p_values = []
        for var in dem_vars:
            res = run_balance_test(panel_joint, var, "bartik", year_fe=True, label=var)
            if res:
                p_values.append(res["p"])

        if p_values:
            # Bonferroni: reject joint null if min(p) < alpha/n_tests
            min_p = min(p_values)
            bonferroni_p = min(min_p * n_outcomes, 1.0)
            print(f"  Bonferroni-corrected min p = {bonferroni_p:.4f} "
                  f"(min individual p = {min_p:.4f}, {n_outcomes} tests)")
            results.append({
                "outcome": "JOINT (demographics, Bonferroni)",
                "bartik_var": "bartik",
                "coef": np.nan,
                "se": np.nan,
                "t": np.nan,
                "p": bonferroni_p,
                "n": len(panel_joint),
                "r2": np.nan,
            })

    # ── Save results ────────────────────────────────────────────────────
    print("\n[5] Saving results...")

    results_df = pd.DataFrame(results)
    out_path = os.path.join(OUT_DIR, "covariate_balance.csv")
    results_df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")

    # Print summary table
    print("\n" + "=" * 80)
    print("COVARIATE BALANCE SUMMARY")
    print("=" * 80)
    print(f"{'Outcome':<30} {'Instrument':<15} {'β':>10} {'SE':>10} {'p':>8} {'N':>8}")
    print("-" * 80)
    for _, row in results_df.iterrows():
        sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else ""
        print(f"{row['outcome']:<30} {row['bartik_var']:<15} "
              f"{row['coef']:>10.4f} {row['se']:>10.4f} {row['p']:>7.3f}{sig} {row['n']:>7.0f}")
    print("=" * 80)

    # Interpretation
    n_sig = sum(1 for _, r in results_df.iterrows()
                if r["bartik_var"] == "bartik" and r["p"] < 0.05
                and "JOINT" not in str(r["outcome"]))
    n_total = sum(1 for _, r in results_df.iterrows()
                  if r["bartik_var"] == "bartik"
                  and "JOINT" not in str(r["outcome"]))

    print(f"\nSignificant at 5%: {n_sig}/{n_total} covariates")
    if n_sig == 0:
        print("✓ PASS: Bartik does not predict observable MSA characteristics")
    elif n_sig <= 1:
        print("~ MARGINAL: 1 covariate significant (could be chance at 5% level)")
    else:
        print("⚠ WARNING: Multiple covariates predicted — check if economically meaningful")


if __name__ == "__main__":
    main()
