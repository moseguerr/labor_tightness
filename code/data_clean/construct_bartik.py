"""
Construct the Bartik Shift-Share Instrument (BHJ 2022 Framework)
================================================================

This script builds the Bartik IV from QCEW county-level employment data,
following Borusyak, Hull & Jaravel (2022) exactly:

    B_{m,t} = Σ_k  s_{m,k,t0} × g_{k,-m,t}

where:
    s_{m,k,t0} = employment share of industry k in MSA m at baseline t0
    g_{k,-m,t}  = leave-one-out national employment growth rate in industry k

Key design choices:
    - Baseline shares fixed at 2005 (5 years before 2010 sample start)
    - 3-digit NAICS, harmonized across the 2022 revision
    - Leave-one-out: national growth excludes the focal MSA
    - Non-traded sectors excluded (44-45 Retail, 72 Accommodation/Food, 92 Government)
    - Shifts winsorized at 1st/99th percentiles
    - Final instrument standardized (mean 0, SD 1) within year

Input:  data/Industry Employment/Processed/{year}.parquet  (2004-2025)
Output: data/bartik/bartik_instrument.parquet  (MSA × quarter)
        data/bartik/bartik_components.parquet   (MSA × industry × quarter, for diagnostics)
"""

import pandas as pd
import numpy as np
import os
import gc
import warnings
warnings.filterwarnings("ignore")

# ── Configuration ──────────────────────────────────────────────────────

DATA_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data"
)
PROC_DIR = os.path.join(DATA_DIR, "Industry Employment", "Processed")
XWALK_PATH = os.path.join(DATA_DIR, "Crosswalks", "qcew-county-msa-csa-crosswalk.xlsx")
OUT_DIR = os.path.join(DATA_DIR, "bartik")
os.makedirs(OUT_DIR, exist_ok=True)

BASELINE_YEAR = 2005      # Fixed shares baseline
SAMPLE_START = 2010       # Analysis window start
WINSOR_LO = 0.01          # Winsorization percentiles
WINSOR_HI = 0.99

# Non-traded sectors to exclude (NAICS 2-digit)
# 44-45: Retail Trade, 72: Accommodation & Food, 92: Public Administration
NON_TRADED_SECTORS = {"44", "45", "72", "92"}

# NAICS 2022 revision: map old 3-digit codes to harmonized codes
# These retail subsectors were consolidated in 2022
NAICS_HARMONIZE = {
    "442": "449",  # Furniture stores → Other retail
    "443": "449",  # Electronics stores → Other retail
    "446": "449",  # Health/personal care → Other retail
    "447": "457",  # Gas stations → Gasoline stations (new code)
    "448": "458",  # Clothing stores → Clothing (new code)
    "451": "459",  # Sports/hobby/book → Other (new code)
    "452": "455",  # General merch → Gen merch (new code)
    "453": "459",  # Misc stores → Other
    "454": "456",  # Nonstore retailers → Nonstore (new code)
    "511": "516",  # Publishing → Information (reclassified)
    "515": "516",  # Broadcasting → Information (reclassified)
}


def load_and_harmonize(year: int) -> pd.DataFrame:
    """Load a processed QCEW parquet and harmonize NAICS codes."""
    path = os.path.join(PROC_DIR, f"{year}.parquet")
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_parquet(path, columns=[
        "NAICS3", "area_fips", "year", "qtr", "month1_emplvl", "avg_wkly_wage"
    ])

    # Harmonize NAICS codes
    df["NAICS3"] = df["NAICS3"].replace(NAICS_HARMONIZE)

    # Re-aggregate after harmonization (some codes merged)
    df = (
        df.groupby(["area_fips", "NAICS3", "year", "qtr"], as_index=False)
        .agg({"month1_emplvl": "sum", "avg_wkly_wage": "mean"})
    )

    return df


def load_fips_to_msa() -> pd.DataFrame:
    """Load the FIPS county → MSA crosswalk."""
    # Use Feb 2013 crosswalk for 2010-2023, Jul 2023 for 2024+
    # For consistency, use Feb 2013 as primary (covers most of our period)
    xw = pd.read_excel(XWALK_PATH, sheet_name="Feb. 2013 Crosswalk")
    xw = xw[["County Code", "MSA Code"]].dropna(subset=["MSA Code"])
    xw.columns = ["area_fips", "msa_code"]

    # Ensure area_fips is zero-padded string
    xw["area_fips"] = xw["area_fips"].astype(str).str.zfill(5)
    xw["msa_code"] = xw["msa_code"].astype(str)

    return xw


def exclude_non_traded(df: pd.DataFrame) -> pd.DataFrame:
    """Remove non-traded sectors based on 2-digit NAICS."""
    sector_2d = df["NAICS3"].str[:2]
    mask = ~sector_2d.isin(NON_TRADED_SECTORS)
    n_before = len(df)
    df = df[mask].copy()
    print(f"  Excluded non-traded sectors: {n_before:,} → {len(df):,} rows")
    return df


def main():
    print("=" * 60)
    print("BARTIK SHIFT-SHARE INSTRUMENT CONSTRUCTION")
    print("Following BHJ (2022) Framework")
    print("=" * 60)

    # ── Step 1: Load FIPS-to-MSA crosswalk ──────────────────────────
    print("\n[1] Loading FIPS-to-MSA crosswalk...")
    xw = load_fips_to_msa()
    print(f"  {len(xw)} county-MSA mappings loaded")

    # ── Step 2: Load and aggregate employment to MSA level ──────────
    print("\n[2] Loading and aggregating county employment to MSA level...")

    all_years = list(range(2004, 2026))
    frames = []

    for year in all_years:
        df = load_and_harmonize(year)
        if df.empty:
            continue

        # Keep only county-level rows (5-digit numeric FIPS, not MSA/state)
        df = df[
            df["area_fips"].str.match(r"^\d{5}$")
            & ~df["area_fips"].str.endswith("000")
        ].copy()

        # Map counties to MSAs
        df = df.merge(xw, on="area_fips", how="inner")

        # Aggregate to MSA × NAICS3 × quarter
        df_msa = (
            df.groupby(["msa_code", "NAICS3", "year", "qtr"], as_index=False)
            .agg({"month1_emplvl": "sum", "avg_wkly_wage": "mean"})
        )
        frames.append(df_msa)

        print(f"  {year}: {len(df_msa):,} MSA × industry × quarter obs")
        del df, df_msa
        gc.collect()

    emp = pd.concat(frames, ignore_index=True)
    del frames
    gc.collect()
    print(f"\n  Total: {len(emp):,} rows, {emp['msa_code'].nunique()} MSAs, "
          f"{emp['NAICS3'].nunique()} industries")

    # ── Step 3: Exclude non-traded sectors ──────────────────────────
    print("\n[3] Excluding non-traded sectors...")
    emp = exclude_non_traded(emp)

    # ── Step 4: Compute baseline shares (fixed at BASELINE_YEAR) ────
    print(f"\n[4] Computing baseline shares (fixed at {BASELINE_YEAR})...")

    # Average across quarters in the baseline year for stability
    base = emp[emp["year"] == BASELINE_YEAR].copy()
    base = (
        base.groupby(["msa_code", "NAICS3"], as_index=False)["month1_emplvl"]
        .mean()
        .rename(columns={"month1_emplvl": "base_emp"})
    )

    # Total MSA employment at baseline
    msa_total = (
        base.groupby("msa_code")["base_emp"]
        .sum()
        .rename("base_total")
        .reset_index()
    )
    base = base.merge(msa_total, on="msa_code", how="left")

    # Shares: s_{m,k,t0} = E_{m,k,t0} / E_{m,t0}
    base["share"] = base["base_emp"] / base["base_total"]

    # Verify shares sum to ~1
    share_sums = base.groupby("msa_code")["share"].sum()
    print(f"  Share sums: mean={share_sums.mean():.4f}, "
          f"min={share_sums.min():.4f}, max={share_sums.max():.4f}")
    print(f"  {len(base)} MSA × industry share observations")

    # Incomplete shares control: S_m = sum_k s_{m,k}
    # (should be 1.0 if all traded sectors covered, <1 if some missing)
    incomplete_shares = share_sums.rename("incomplete_shares_sum").reset_index()

    shares = base[["msa_code", "NAICS3", "share", "base_emp"]].copy()

    # ── Step 5: Compute leave-one-out national growth rates ─────────
    print("\n[5] Computing leave-one-out national employment growth rates...")

    # National employment by industry × quarter (summed across all MSAs)
    nat_emp = (
        emp.groupby(["NAICS3", "year", "qtr"], as_index=False)["month1_emplvl"]
        .sum()
        .rename(columns={"month1_emplvl": "nat_emp"})
    )

    # Merge national totals back to MSA-level data
    emp = emp.merge(nat_emp, on=["NAICS3", "year", "qtr"], how="left")

    # Leave-one-out national employment: E_{k,-m,t} = E_{k,nat,t} - E_{k,m,t}
    emp["loo_emp"] = emp["nat_emp"] - emp["month1_emplvl"]

    # Sort for lag computation
    emp = emp.sort_values(["msa_code", "NAICS3", "year", "qtr"]).reset_index(drop=True)

    # Create a period index for proper lagging (year × quarter → single index)
    emp["period"] = emp["year"] * 10 + emp["qtr"]

    # Lag: previous quarter's LOO employment
    emp["loo_emp_lag"] = (
        emp.groupby(["msa_code", "NAICS3"])["loo_emp"]
        .shift(1)
    )

    # Also need to verify the lag is actually the previous quarter (no gaps)
    emp["period_lag"] = emp.groupby(["msa_code", "NAICS3"])["period"].shift(1)

    # Expected previous period
    def prev_period(p):
        year, qtr = divmod(p, 10)
        if qtr == 1:
            return (year - 1) * 10 + 4
        return year * 10 + (qtr - 1)

    emp["expected_prev"] = emp["period"].apply(prev_period)
    # Set lag to NaN if there's a gap
    gap_mask = emp["period_lag"] != emp["expected_prev"]
    emp.loc[gap_mask, "loo_emp_lag"] = np.nan

    # LOO growth rate: g_{k,-m,t} = E_{k,-m,t} / E_{k,-m,t-1} - 1
    emp["shift"] = emp["loo_emp"] / emp["loo_emp_lag"] - 1

    # Handle division issues
    emp.loc[emp["loo_emp_lag"] == 0, "shift"] = np.nan
    emp.loc[emp["loo_emp_lag"].isna(), "shift"] = np.nan

    print(f"  Shifts computed: {emp['shift'].notna().sum():,} non-null out of {len(emp):,}")
    print(f"  Shift stats: mean={emp['shift'].mean():.4f}, "
          f"std={emp['shift'].std():.4f}, "
          f"min={emp['shift'].min():.4f}, max={emp['shift'].max():.4f}")

    # ── Step 6: Winsorize shifts ────────────────────────────────────
    print(f"\n[6] Winsorizing shifts at [{WINSOR_LO:.0%}, {WINSOR_HI:.0%}]...")
    lo_val = emp["shift"].quantile(WINSOR_LO)
    hi_val = emp["shift"].quantile(WINSOR_HI)
    emp["shift_w"] = emp["shift"].clip(lower=lo_val, upper=hi_val)
    print(f"  Clipped to [{lo_val:.4f}, {hi_val:.4f}]")

    # ── Step 7: Assemble the instrument ─────────────────────────────
    print("\n[7] Assembling Bartik instrument...")

    # Keep only sample period (need shifts, so start from SAMPLE_START)
    emp_sample = emp[emp["year"] >= SAMPLE_START].copy()

    # Merge baseline shares
    emp_sample = emp_sample.merge(
        shares[["msa_code", "NAICS3", "share"]],
        on=["msa_code", "NAICS3"],
        how="inner",
    )

    # Component: s_{m,k,t0} × g_{k,-m,t}
    emp_sample["component"] = emp_sample["share"] * emp_sample["shift_w"]

    # Save components for diagnostics
    components = emp_sample[[
        "msa_code", "NAICS3", "year", "qtr", "share", "shift_w",
        "component", "month1_emplvl", "nat_emp", "loo_emp",
    ]].copy()
    components.to_parquet(
        os.path.join(OUT_DIR, "bartik_components.parquet"),
        compression="zstd", index=False,
    )
    print(f"  Saved components: {len(components):,} rows")

    # Aggregate to MSA × quarter: B_{m,t} = Σ_k component
    bartik = (
        emp_sample.groupby(["msa_code", "year", "qtr"], as_index=False)
        .agg(
            bartik_raw=("component", "sum"),
            n_industries=("component", "count"),
            n_nonzero=("component", lambda x: (x != 0).sum()),
        )
    )

    # ── Step 7b: No-NAICS-611 variant (robustness) ────────────────
    # NAICS 611 (Education) has extreme serial correlation (ρ=0.94 annual)
    # and carries ~31% Rotemberg weight. Build instrument without it.
    print("\n[7b] Building no-NAICS-611 robustness variant...")
    emp_no611 = emp_sample[emp_sample["NAICS3"] != "611"]
    bartik_no611 = (
        emp_no611.groupby(["msa_code", "year", "qtr"], as_index=False)
        .agg(bartik_raw_no611=("component", "sum"))
    )
    bartik = bartik.merge(bartik_no611, on=["msa_code", "year", "qtr"], how="left")
    print(f"  No-611 variant computed for {len(bartik_no611):,} obs")

    # Merge incomplete shares control
    bartik = bartik.merge(incomplete_shares, on="msa_code", how="left")

    # ── Step 8: Standardize within year ─────────────────────────────
    print("\n[8] Standardizing instrument within year...")

    bartik["bartik"] = bartik.groupby("year")["bartik_raw"].transform(
        lambda x: (x - x.mean()) / x.std()
    )
    bartik["bartik_no611"] = bartik.groupby("year")["bartik_raw_no611"].transform(
        lambda x: (x - x.mean()) / x.std()
    )

    # ── Step 8b: Compute 4-quarter lagged instrument (JRS control) ──
    print("\n[8b] Computing 4-quarter lagged instrument for JRS dynamic control...")
    bartik = bartik.sort_values(["msa_code", "year", "qtr"]).reset_index(drop=True)
    bartik["period"] = bartik["year"] * 10 + bartik["qtr"]
    bartik["bartik_lag4"] = bartik.groupby("msa_code")["bartik"].shift(4)
    bartik["period_lag4"] = bartik.groupby("msa_code")["period"].shift(4)
    # Verify the lag is exactly 4 quarters back (1 year)
    bartik["expected_lag4"] = bartik["period"].apply(lambda p: (p // 10 - 1) * 10 + p % 10)
    gap_mask = bartik["period_lag4"] != bartik["expected_lag4"]
    bartik.loc[gap_mask, "bartik_lag4"] = np.nan
    bartik.drop(columns=["period", "period_lag4", "expected_lag4"], inplace=True)
    n_lag4 = bartik["bartik_lag4"].notna().sum()
    print(f"  Lagged instrument available for {n_lag4:,} of {len(bartik):,} obs")

    print(f"\n  Final instrument: {len(bartik):,} MSA × quarter obs")
    print(f"  Years: {bartik['year'].min()}-{bartik['year'].max()}")
    print(f"  MSAs: {bartik['msa_code'].nunique()}")
    print(f"  Mean industries per MSA-quarter: {bartik['n_industries'].mean():.1f}")

    # Summary stats by year
    print("\n  Year-level summary:")
    for year, grp in bartik.groupby("year"):
        print(f"    {year}: n={len(grp):>4}, mean={grp['bartik'].mean():>7.3f}, "
              f"sd={grp['bartik'].std():.3f}, "
              f"raw_mean={grp['bartik_raw'].mean():.5f}")

    # ── Step 9: Save ────────────────────────────────────────────────
    print("\n[9] Saving...")

    # Extract numeric MSA code for matching with regression data
    bartik["BestFitMSA4"] = (
        bartik["msa_code"]
        .str.replace("C", "", regex=False)
        .astype(int)
    )

    out_path = os.path.join(OUT_DIR, "bartik_instrument.parquet")
    bartik.to_parquet(out_path, compression="zstd", index=False)
    print(f"  ✅ Saved: {out_path}")

    # Also save a summary
    summary = {
        "baseline_year": BASELINE_YEAR,
        "sample_years": f"{bartik['year'].min()}-{bartik['year'].max()}",
        "n_msas": bartik["msa_code"].nunique(),
        "n_industries": emp_sample["NAICS3"].nunique(),
        "n_obs": len(bartik),
        "excluded_sectors": list(NON_TRADED_SECTORS),
        "naics_harmonized": NAICS_HARMONIZE,
        "winsorization": [WINSOR_LO, WINSOR_HI],
        "columns": {
            "bartik": "Primary instrument (standardized within year)",
            "bartik_no611": "Robustness: excludes NAICS 611 (Education)",
            "bartik_lag4": "4-quarter lagged instrument (JRS dynamic control)",
            "bartik_raw": "Unstandardized instrument",
            "bartik_raw_no611": "Unstandardized no-611 variant",
        },
    }
    print(f"\n  Summary: {summary}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
