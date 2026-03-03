"""
Bartik Instrument — Robustness Variants
========================================

Constructs two additional instrument variants for the appendix:

1. Alternative baseline year (2007 instead of 2005)
   - Tests sensitivity to baseline share period
   - Per Bai (2025): multiple baselines strengthen share exogeneity argument

2. State-level geographic leave-out
   - National growth excluding the entire STATE (not just MSA)
   - Guards against within-state regional spillovers
   - Per Bai (2025): broader geographic exclusions as robustness

Output: data/bartik/bartik_robustness.parquet
    Columns: BestFitMSA4, year, qtr, bartik_base2007, bartik_state_loo
"""

import pandas as pd
import numpy as np
import os
import gc
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
PROC_DIR = os.path.join(DATA_DIR, "Industry Employment", "Processed")
XWALK_PATH = os.path.join(DATA_DIR, "Crosswalks", "qcew-county-msa-csa-crosswalk.xlsx")
OUT_DIR = os.path.join(DATA_DIR, "bartik")

SAMPLE_START = 2010
WINSOR_LO = 0.01
WINSOR_HI = 0.99

NON_TRADED_SECTORS = {"44", "45", "72", "92"}

NAICS_HARMONIZE = {
    "442": "449", "443": "449", "446": "449", "447": "457",
    "448": "458", "451": "459", "452": "455", "453": "459",
    "454": "456", "511": "516", "515": "516",
}


def load_and_harmonize(year):
    path = os.path.join(PROC_DIR, f"{year}.parquet")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_parquet(path, columns=[
        "NAICS3", "area_fips", "year", "qtr", "month1_emplvl"
    ], engine="fastparquet")
    df["NAICS3"] = df["NAICS3"].replace(NAICS_HARMONIZE)
    df = (
        df.groupby(["area_fips", "NAICS3", "year", "qtr"], as_index=False)
        .agg({"month1_emplvl": "sum"})
    )
    return df


def load_fips_to_msa():
    xw = pd.read_excel(XWALK_PATH, sheet_name="Feb. 2013 Crosswalk")
    xw = xw[["County Code", "MSA Code"]].dropna(subset=["MSA Code"])
    xw.columns = ["area_fips", "msa_code"]
    xw["area_fips"] = xw["area_fips"].astype(str).str.zfill(5)
    xw["msa_code"] = xw["msa_code"].astype(str)
    # Extract state FIPS from county code (first 2 digits)
    xw["state_fips"] = xw["area_fips"].str[:2]
    return xw


def exclude_non_traded(df):
    sector_2d = df["NAICS3"].str[:2]
    return df[~sector_2d.isin(NON_TRADED_SECTORS)].copy()


def compute_shares(emp, baseline_year):
    """Compute baseline employment shares for a given year."""
    base = emp[emp["year"] == baseline_year].copy()
    base = (
        base.groupby(["msa_code", "NAICS3"], as_index=False)["month1_emplvl"]
        .mean()
        .rename(columns={"month1_emplvl": "base_emp"})
    )
    msa_total = (
        base.groupby("msa_code")["base_emp"]
        .sum()
        .rename("base_total")
        .reset_index()
    )
    base = base.merge(msa_total, on="msa_code")
    base["share"] = base["base_emp"] / base["base_total"]
    return base[["msa_code", "NAICS3", "share"]]


def compute_msa_loo_shifts(emp):
    """Standard LOO: exclude focal MSA from national growth."""
    nat_emp = (
        emp.groupby(["NAICS3", "year", "qtr"], as_index=False)["month1_emplvl"]
        .sum()
        .rename(columns={"month1_emplvl": "nat_emp"})
    )
    emp = emp.merge(nat_emp, on=["NAICS3", "year", "qtr"])
    emp["loo_emp"] = emp["nat_emp"] - emp["month1_emplvl"]

    emp = emp.sort_values(["msa_code", "NAICS3", "year", "qtr"]).reset_index(drop=True)
    emp["period"] = emp["year"] * 10 + emp["qtr"]
    emp["loo_emp_lag"] = emp.groupby(["msa_code", "NAICS3"])["loo_emp"].shift(1)
    emp["period_lag"] = emp.groupby(["msa_code", "NAICS3"])["period"].shift(1)

    def prev_period(p):
        year, qtr = divmod(p, 10)
        if qtr == 1:
            return (year - 1) * 10 + 4
        return year * 10 + (qtr - 1)

    emp["expected_prev"] = emp["period"].apply(prev_period)
    gap_mask = emp["period_lag"] != emp["expected_prev"]
    emp.loc[gap_mask, "loo_emp_lag"] = np.nan

    emp["shift"] = emp["loo_emp"] / emp["loo_emp_lag"] - 1
    emp.loc[emp["loo_emp_lag"] == 0, "shift"] = np.nan
    emp.loc[emp["loo_emp_lag"].isna(), "shift"] = np.nan

    lo_val = emp["shift"].quantile(WINSOR_LO)
    hi_val = emp["shift"].quantile(WINSOR_HI)
    emp["shift_w"] = emp["shift"].clip(lower=lo_val, upper=hi_val)

    return emp


def compute_state_loo_shifts(emp):
    """State-level LOO: exclude entire state from national growth."""
    # Need state FIPS from the MSA-state mapping
    # State employment by industry × quarter
    state_emp = (
        emp.groupby(["state_fips", "NAICS3", "year", "qtr"], as_index=False)["month1_emplvl"]
        .sum()
        .rename(columns={"month1_emplvl": "state_emp"})
    )

    nat_emp = (
        emp.groupby(["NAICS3", "year", "qtr"], as_index=False)["month1_emplvl"]
        .sum()
        .rename(columns={"month1_emplvl": "nat_emp"})
    )

    # For each MSA, identify its primary state
    msa_state = (
        emp.groupby(["msa_code", "state_fips"], as_index=False)["month1_emplvl"]
        .sum()
    )
    # Assign MSA to the state with the most employment
    msa_primary_state = (
        msa_state.sort_values("month1_emplvl", ascending=False)
        .drop_duplicates(subset=["msa_code"], keep="first")
        [["msa_code", "state_fips"]]
    )

    # Merge state info into MSA-level data
    emp = emp.merge(msa_primary_state.rename(columns={"state_fips": "primary_state"}),
                    on="msa_code", how="left")

    # National minus state employment
    emp = emp.merge(nat_emp, on=["NAICS3", "year", "qtr"])
    emp = emp.merge(state_emp.rename(columns={"state_fips": "primary_state"}),
                    on=["primary_state", "NAICS3", "year", "qtr"], how="left")
    emp["state_emp"] = emp["state_emp"].fillna(0)
    emp["loo_state_emp"] = emp["nat_emp"] - emp["state_emp"]

    emp = emp.sort_values(["msa_code", "NAICS3", "year", "qtr"]).reset_index(drop=True)
    emp["period"] = emp["year"] * 10 + emp["qtr"]
    emp["loo_state_lag"] = emp.groupby(["msa_code", "NAICS3"])["loo_state_emp"].shift(1)
    emp["period_lag"] = emp.groupby(["msa_code", "NAICS3"])["period"].shift(1)

    def prev_period(p):
        year, qtr = divmod(p, 10)
        if qtr == 1:
            return (year - 1) * 10 + 4
        return year * 10 + (qtr - 1)

    emp["expected_prev"] = emp["period"].apply(prev_period)
    gap_mask = emp["period_lag"] != emp["expected_prev"]
    emp.loc[gap_mask, "loo_state_lag"] = np.nan

    emp["shift_state"] = emp["loo_state_emp"] / emp["loo_state_lag"] - 1
    emp.loc[emp["loo_state_lag"] == 0, "shift_state"] = np.nan
    emp.loc[emp["loo_state_lag"].isna(), "shift_state"] = np.nan

    lo_val = emp["shift_state"].quantile(WINSOR_LO)
    hi_val = emp["shift_state"].quantile(WINSOR_HI)
    emp["shift_state_w"] = emp["shift_state"].clip(lower=lo_val, upper=hi_val)

    return emp


def assemble_bartik(emp_sample, shares, shift_col="shift_w", name="bartik"):
    """Assemble the Bartik instrument from shares and shifts."""
    merged = emp_sample.merge(
        shares, on=["msa_code", "NAICS3"], how="inner"
    )
    merged["component"] = merged["share"] * merged[shift_col]

    result = (
        merged.groupby(["msa_code", "year", "qtr"], as_index=False)
        .agg(**{f"{name}_raw": ("component", "sum")})
    )

    # Standardize within year
    result[name] = result.groupby("year")[f"{name}_raw"].transform(
        lambda x: (x - x.mean()) / x.std()
    )

    return result


def main():
    print("=" * 60)
    print("BARTIK ROBUSTNESS VARIANTS")
    print("=" * 60)

    # ── Load data ──────────────────────────────────────────────────────
    print("\n[1] Loading data...")
    xw = load_fips_to_msa()

    frames = []
    for year in range(2004, 2026):
        df = load_and_harmonize(year)
        if df.empty:
            continue
        df = df[
            df["area_fips"].str.match(r"^\d{5}$")
            & ~df["area_fips"].str.endswith("000")
        ].copy()
        # Keep state_fips from area_fips (first 2 digits)
        df["state_fips"] = df["area_fips"].str[:2]
        df = df.merge(xw[["area_fips", "msa_code"]], on="area_fips", how="inner")
        df_msa = (
            df.groupby(["msa_code", "state_fips", "NAICS3", "year", "qtr"], as_index=False)
            .agg({"month1_emplvl": "sum"})
        )
        frames.append(df_msa)
        print(f"  {year}: {len(df_msa):,} rows")
        del df, df_msa
        gc.collect()

    emp = pd.concat(frames, ignore_index=True)
    del frames
    gc.collect()

    emp = exclude_non_traded(emp)
    print(f"  Total: {len(emp):,} rows")

    # ── Variant 1: Alternative baseline (2007) ─────────────────────────
    print("\n[2] Computing alternative baseline shares (2007)...")
    shares_2007 = compute_shares(emp, baseline_year=2007)
    n_msas_2007 = shares_2007["msa_code"].nunique()
    print(f"  2007 baseline: {len(shares_2007)} MSA × industry ({n_msas_2007} MSAs)")

    # Standard MSA-level LOO shifts (reuse same shifts, different shares)
    # Collapse to MSA level first (emp has state_fips granularity for state LOO)
    print("\n[3] Computing MSA-level LOO shifts...")
    emp_msa = (
        emp.groupby(["msa_code", "NAICS3", "year", "qtr"], as_index=False)["month1_emplvl"]
        .sum()
    )
    emp_shifted = compute_msa_loo_shifts(emp_msa)
    emp_sample = emp_shifted[emp_shifted["year"] >= SAMPLE_START].copy()

    bartik_2007 = assemble_bartik(emp_sample, shares_2007, "shift_w", "bartik_base2007")
    print(f"  Alternative baseline instrument: {len(bartik_2007):,} obs")

    # ── Variant 2: State-level leave-out ───────────────────────────────
    print("\n[4] Computing state-level LOO shifts...")
    emp_state = compute_state_loo_shifts(emp.copy())
    emp_state_sample = emp_state[emp_state["year"] >= SAMPLE_START].copy()

    # Use primary (2005) baseline shares for this variant
    shares_2005 = compute_shares(emp, baseline_year=2005)
    bartik_state = assemble_bartik(emp_state_sample, shares_2005, "shift_state_w", "bartik_state_loo")
    print(f"  State LOO instrument: {len(bartik_state):,} obs")

    # ── Merge variants ─────────────────────────────────────────────────
    print("\n[5] Merging and saving...")

    result = bartik_2007[["msa_code", "year", "qtr", "bartik_base2007"]].merge(
        bartik_state[["msa_code", "year", "qtr", "bartik_state_loo"]],
        on=["msa_code", "year", "qtr"],
        how="outer",
    )

    # Add 4-digit MSA code for merging with regressions
    result["BestFitMSA4"] = (
        result["msa_code"]
        .str.replace("C", "", regex=False)
        .astype(int)
    )

    out_path = os.path.join(OUT_DIR, "bartik_robustness.parquet")
    result.to_parquet(out_path, compression="zstd", index=False)
    print(f"  Saved: {out_path}")
    print(f"  {len(result):,} obs, {result['msa_code'].nunique()} MSAs")

    # Correlation with primary instrument
    primary = pd.read_parquet(os.path.join(OUT_DIR, "bartik_instrument.parquet"),
                             engine="fastparquet")
    merged = result.merge(
        primary[["BestFitMSA4", "year", "qtr", "bartik"]],
        on=["BestFitMSA4", "year", "qtr"],
        how="inner",
    )
    if len(merged) > 100:
        corr_2007 = merged[["bartik", "bartik_base2007"]].corr().iloc[0, 1]
        corr_state = merged[["bartik", "bartik_state_loo"]].corr().iloc[0, 1]
        print(f"\n  Correlation with primary bartik:")
        print(f"    Alternative baseline (2007): r = {corr_2007:.4f}")
        print(f"    State-level LOO:             r = {corr_state:.4f}")

    # Summary statistics
    print(f"\n  Summary stats:")
    for col in ["bartik_base2007", "bartik_state_loo"]:
        vals = result[col].dropna()
        print(f"    {col}: mean={vals.mean():.3f}, sd={vals.std():.3f}, "
              f"n={len(vals)}, min={vals.min():.3f}, max={vals.max():.3f}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
