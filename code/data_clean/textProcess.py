import pandas as pd
import os
import glob
import gc
import re

def extract_months_from_filename(filename):
    """
    Extracts month(s) from filenames like:
    - US_XML_AddFeed_20101126_20101202.parquet
    - US_XML_AddFeed_20140217_20140223.parquet
    Returns a list of months.
    """
    match = re.search(r'_(\d{4})(\d{2})\d{2}_(\d{4})(\d{2})\d{2}\.parquet', filename)
    if match:
        start_year, start_month, end_year, end_month = match.groups()
        return [start_month, end_month] if start_year == end_year and start_month != end_month else [start_month]
    else:
        match = re.search(r'_(\d{4})(\d{2})\d{2}\.parquet', filename)
        return [match.group(2)] if match else []

def process_month_text(year, input_base_directory, output_base_directory):
    """
    Processes and merges monthly Parquet files for a given year.
    If a file spans two months, it correctly assigns observations to the respective month.
    """
    input_directory = os.path.join(input_base_directory, str(year), "read_dictionaries")
    output_directory = os.path.join(output_base_directory, f"merge_main/{year}")
    os.makedirs(output_directory, exist_ok=True)

    # Dictionary to store files associated with each month
    month_files = {f"{month:02d}": [] for month in range(1, 13)}
    spanning_files = {}

    # Get all Parquet files in the directory
    all_files = sorted(glob.glob(os.path.join(input_directory, "US_XML_AddFeed_*.parquet")))

    for file_path in all_files:
        filename = os.path.basename(file_path)
        file_months = extract_months_from_filename(filename)

        for month in file_months:
            if len(file_months) == 1:
                month_files[month].append(file_path)  # Regular single-month file
            else:
                spanning_files[file_path] = file_months  # Store spanning files separately

    # ✅ Process each month separately (avoiding memory overload)
    for month in month_files.keys():
        month_str = str(month).zfill(2)
        print(f"Processing {year}-{month_str}...")

        df_txt = None  # Initialize empty DataFrame


        # ✅ Load only the relevant files for this month
        for file in month_files[month]:
            df = pd.read_parquet(file, engine="pyarrow")  # Read only one file
            df_txt = df if df_txt is None else pd.concat([df_txt, df], ignore_index=True)
            del df  # Free memory after loading
            gc.collect()

        # ✅ Handle spanning files (load only rows relevant to the month)
        for file_path, file_months in spanning_files.items():
            if month in file_months:
                df_span = pd.read_parquet(file_path, engine="pyarrow")
                df_span = df_span[df_span['month'].astype(str).str.zfill(2) == month_str]
                df_txt = df_span if df_txt is None else pd.concat([df_txt, df_span], ignore_index=True)
                del df_span  # Free memory
                gc.collect()

        if df_txt is not None:
            # ✅ Process the dataset
            df_txt['length'] = df_txt['CleanText'].str.split().str.len()
            df_txt.rename(columns={'JobID': 'BGTJobId'}, errors='ignore', inplace=True)
            df_txt.drop(columns=['CanonEmployer', 'JobDate', 'JobText', 'CleanText', 'year'], inplace=True, errors='ignore')

            # ✅ Save the processed file
            output_file_path = os.path.join(output_directory, f"Text_{year}-{month_str}.parquet")
            df_txt.to_parquet(output_file_path, engine="pyarrow", compression='zstd')

            # ✅ Free memory immediately after saving
            del df_txt
            gc.collect()

            print(f"Saved: {output_file_path}")

    print(f"Finished processing year {year}.")