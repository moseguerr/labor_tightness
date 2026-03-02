#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 20:44:12 2025
@author: mgor
"""

import os
import re
import gc
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from scipy.stats import entropy
from concurrent.futures import ProcessPoolExecutor


def rename_column(col_name):
    """Cleans and renames column names using camelCase."""
    if col_name.lower() == 'na':
        return 'notMapped'
    
    if ' ' in col_name:
        cleaned_name = re.sub(r',', '', col_name)
        cleaned_name = re.sub(r'\band\b', '', cleaned_name, flags=re.IGNORECASE)
        words = cleaned_name.split()
        return words[0].lower() + words[1].capitalize() if len(words) > 1 else words[0].lower()

    return col_name  # Return original name if no changes needed


def process_single_file(file_name, input_path, output_path):
    """
    Processes a single ZIP file and saves the output as a Parquet file.
    """
    input_file_path = os.path.join(input_path, file_name)
    output_file_name = file_name.replace('.zip', '.parquet')
    output_file_path = os.path.join(output_path, output_file_name)

    print(f"📂 Processing file: {file_name}")  # Debug print

    if not os.path.exists(input_file_path):
        print(f"❌ File does not exist: {input_file_path}")
        return

    try:
        # ✅ Read the file
        df = pd.read_table(input_file_path, encoding='latin')
        print(f"✅ Read {len(df)} rows from {input_file_path}")

        # ✅ One-hot encode categorical column
        encoder = OneHotEncoder(sparse_output=True, dtype=int)
        encoded = encoder.fit_transform(df[['SkillClusterFamily']])
        encoded_df = pd.DataFrame.sparse.from_spmatrix(
            encoded, columns=encoder.get_feature_names_out(['SkillClusterFamily'])
        )
        encoded_df.columns = [col.replace('SkillClusterFamily_', '') for col in encoded_df.columns]

        # ✅ Merge with original DataFrame
        df = pd.concat([df.reset_index(drop=True), encoded_df.reset_index(drop=True)], axis=1)

        # ✅ Apply renaming logic
        df = df.rename(columns={col: rename_column(col) for col in df.columns})

        # ✅ Compute feature aggregations
        df['SkillsCount'] = df.groupby('BGTJobId')['Skill'].transform('nunique')
        df['SkillClusterCount'] = df.groupby('BGTJobId')['SkillCluster'].transform('nunique')
        df['SkillClusterbyFam'] = df.groupby(['BGTJobId', 'SkillClusterFamily'])['SkillCluster'].transform('nunique')
        df['SkillFamilyCount'] = df.groupby('BGTJobId')['SkillClusterFamily'].transform('nunique')
        df['ClusterToFamilyRatio'] = df['SkillClusterbyFam'] / df['SkillFamilyCount']

        total_families = df['SkillClusterFamily'].nunique()
        df['SkillFamilyCoverage'] = df['SkillFamilyCount'] / total_families

        def calculate_entropy(series):
            counts = series.value_counts(normalize=True)
            return entropy(counts)

        df['SkillFamilyEntropy'] = df.groupby('BGTJobId')['SkillClusterFamily'].transform(calculate_entropy)

        # ✅ Drop unnecessary columns
        df.drop(columns=['JobDate', 'Skill', 'SkillCluster', 'SkillClusterFamily', 'Salary'], inplace=True, errors='ignore')

        # ✅ Convert sparse columns to dense
        sparse_cols = [col for col in df.columns if pd.api.types.is_sparse(df[col])]
        df[sparse_cols] = df[sparse_cols].sparse.to_dense()

        # ✅ Aggregate data to BGTJobId level
        df = df.groupby('BGTJobId').mean().reset_index()

        # ✅ Save to Parquet (no threading needed for writing)
        df.to_parquet(output_file_path, engine="pyarrow", compression='zstd', index=False)
        print(f"✔ Saved: {output_file_path}")

        # ✅ Free memory
        del df
        gc.collect()

    except Exception as e:
        print(f"❌ Error processing {file_name}: {e}")


def process_skill_files(year, main_directory, output_directory, max_workers=4):
    """
    Parallelizes processing of all files for a given year.
    """
    input_path = os.path.join(main_directory, year)
    output_path = os.path.join(output_directory, year)

    # ✅ Ensure year-specific output directory exists
    os.makedirs(output_path, exist_ok=True)

    # ✅ List all files in the input directory
    files = [f for f in os.listdir(input_path) if f.endswith('.zip')]

    if not files:
        print(f"⚠️ No ZIP files found for {year} in {input_path}")
        return

    print(f"📂 Processing {len(files)} files for {year}...")

    # ✅ Parallelize file processing (Fix: Removed `lambda`)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file_name in files:
            futures.append(executor.submit(process_single_file, file_name, input_path, output_path))

        for future in futures:
            future.result()  # Ensures all processes complete and raises errors if any fail

    print(f"✅ Finished processing year {year}.")


# ✅ Run the function (adjust paths)
if __name__ == "__main__":
    # Define the years and directories
    years = [str(year) for year in range(2010, 2022)]
    main_directory = '/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Skill/'
    output_directory = '/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'

    for year in years:
        process_skill_files(year, main_directory, output_directory, max_workers=6)
