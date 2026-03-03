"""
Process QCEW quarterly single-file ZIPs for 2022-2025.
Matches the format of existing processed parquets in:
    data/Industry Employment/Processed/{year}.parquet

Output columns: NAICS3, area_fips, year, qtr, month1_emplvl,
    taxable_qtrly_wages, qtrly_contributions, LNAICSShare,
    NatShare, NAICSShare, avg_wkly_wage

Preserves county-level, MSA-level, and state-level area_fips codes.
Aggregates 6-digit NAICS to 3-digit.
"""

import pandas as pd
import numpy as np
import os
import gc

# Paths
RAW_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data/Industry Employment/Raw"
)
OUT_DIR = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox/labor_tightness/data/Industry Employment/Processed"
)
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = [2022, 2023, 2024, 2025]

for year in YEARS:
    zip_path = os.path.join(RAW_DIR, f"{year}_qtrly_singlefile.zip")
    out_path = os.path.join(OUT_DIR, f"{year}.parquet")

    if os.path.exists(out_path):
        print(f"⏭️  {year}: already exists, skipping")
        continue

    if not os.path.exists(zip_path):
        print(f"⚠️  {year}: ZIP not found at {zip_path}, skipping")
        continue

    print(f"🔄 Processing {year}...")

    # Read raw QCEW quarterly single file
    df = pd.read_csv(
        zip_path,
        compression="zip",
        dtype={"industry_code": str, "area_fips": str, "own_code": str},
        usecols=[
            "area_fips", "own_code", "industry_code", "year", "qtr",
            "month1_emplvl", "taxable_qtrly_wages", "qtrly_contributions",
            "avg_wkly_wage",
        ],
    )
    print(f"  Raw rows: {len(df):,}")

    # Keep only 6-digit NAICS codes (matches existing notebook logic)
    df = df[df["industry_code"].str.len() == 6].copy()
    # Exclude own_code == 0 (not applicable)
    df = df[df["own_code"] != "0"]
    # Exclude industry codes starting with '10' (total all industries)
    df = df[~df["industry_code"].str.startswith("10")]

    # Create NAICS3 (first 3 digits of 6-digit code)
    df["NAICS3"] = df["industry_code"].str[:3]

    # Aggregate to NAICS3 level: sum employment/wages, mean weekly wage
    agg_dict = {
        "month1_emplvl": "sum",
        "taxable_qtrly_wages": "sum",
        "qtrly_contributions": "sum",
        "avg_wkly_wage": "mean",
    }
    df = (
        df.groupby(["area_fips", "NAICS3", "year", "qtr"], as_index=False)
        .agg(agg_dict)
    )

    # Fill missing combinations with zeros (cross join all area × NAICS3 × qtr)
    unique_areas = df[["area_fips"]].drop_duplicates()
    unique_naics = pd.DataFrame({"NAICS3": df["NAICS3"].unique()})
    unique_qtrs = pd.DataFrame({"qtr": df["qtr"].unique()})

    complete_index = (
        unique_areas.merge(unique_naics, how="cross")
        .merge(unique_qtrs, how="cross")
    )
    complete_index["year"] = year

    df = complete_index.merge(
        df, on=["area_fips", "NAICS3", "year", "qtr"], how="left"
    )
    fill_cols = ["month1_emplvl", "taxable_qtrly_wages", "qtrly_contributions"]
    df[fill_cols] = df[fill_cols].fillna(0)

    df = df.sort_values(["area_fips", "year", "NAICS3", "qtr"]).reset_index(drop=True)

    # --- Compute shares (matching existing notebook logic) ---

    # Separate national (US000) and non-national
    df_nat = df[df["area_fips"] == "US000"].copy()
    df_local = df[df["area_fips"] != "US000"].copy()

    # National share: NatShare = industry emp / total national emp per quarter
    nat_total = (
        df_nat.groupby("qtr")["month1_emplvl"]
        .sum()
        .rename("total_nat_emp")
        .reset_index()
    )
    df_nat = df_nat.merge(nat_total, on="qtr", how="left")
    df_nat["NatShare"] = (df_nat["month1_emplvl"] / df_nat["total_nat_emp"]) * 100
    df_nat = df_nat[["NAICS3", "qtr", "month1_emplvl", "NatShare"]].rename(
        columns={"month1_emplvl": "nationEmp"}
    )

    # Local share: LNAICSShare = local industry emp / total local emp per area-quarter
    local_total = (
        df_local.groupby(["area_fips", "qtr"])["month1_emplvl"]
        .sum()
        .rename("totEmp")
        .reset_index()
    )
    df_local = df_local.merge(local_total, on=["area_fips", "qtr"], how="left")
    df_local["LNAICSShare"] = (df_local["month1_emplvl"] / df_local["totEmp"]) * 100
    df_local.drop(columns=["totEmp"], inplace=True)

    # Merge national data
    df_local = df_local.merge(df_nat, on=["NAICS3", "qtr"], how="left")

    # Leave-one-out share: NAICSShare = (national - local) / sum(national - local)
    df_local["excludedOcc"] = df_local["nationEmp"] - df_local["month1_emplvl"]
    excl_total = (
        df_local.groupby("area_fips")["excludedOcc"]
        .sum()
        .rename("excludedTotal")
        .reset_index()
    )
    df_local = df_local.merge(excl_total, on="area_fips", how="left")
    df_local["NAICSShare"] = (df_local["excludedOcc"] / df_local["excludedTotal"]) * 100

    # Clean up
    df_local.drop(
        columns=["nationEmp", "excludedOcc", "excludedTotal"], inplace=True
    )
    df_local.drop_duplicates(
        subset=["area_fips", "NAICS3", "qtr"], inplace=True
    )

    # Ensure correct column order and types
    output_cols = [
        "NAICS3", "area_fips", "year", "qtr", "month1_emplvl",
        "taxable_qtrly_wages", "qtrly_contributions", "LNAICSShare",
        "NatShare", "NAICSShare", "avg_wkly_wage",
    ]
    df_out = df_local[output_cols].copy()

    # Save
    df_out.to_parquet(out_path, compression="zstd", engine="pyarrow", index=False)
    print(f"✅ Saved {out_path} ({len(df_out):,} rows)")

    del df, df_nat, df_local, df_out
    gc.collect()

print("\n🎉 All years processed.")
