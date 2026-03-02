import glob
import pandas as pd
import os
import gc

# Limit threading to prevent excessive CPU use
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

# Define the range of years
years = [str(year) for year in range(2010, 2023)]

# Define the main path
main_path = "/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/"

# Define output path for the final merged dataset
output_path = "/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/full_dataset.parquet"

# List to store DataFrames
df_list = []

# Find and process all Parquet files that start with "Aggregated_"
parquet_files = []
for year in years:
    input_path = os.path.join(main_path, year)
    file_pattern = os.path.join(input_path, "Aggregated_*.parquet")
    parquet_files.extend(glob.glob(file_pattern))

print(f"Found {len(parquet_files)} Parquet files. Merging them into a single dataset...")

# Process and append all files
for file in parquet_files:
    df = pd.read_parquet(file)

    # Convert object columns to category for memory efficiency
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype("category")

    df_list.append(df)  # Append to list
    del df  # Free memory
    gc.collect()

# Concatenate all DataFrames into a single DataFrame
df_all = pd.concat(df_list, ignore_index=True)

# Save the final dataset as a single optimized Parquet file
df_all.to_parquet(output_path, engine="pyarrow", compression="zstd", index=False)

# Free memory
del df_list, df_all
gc.collect()

print(f"Dataset successfully saved: {output_path}")
