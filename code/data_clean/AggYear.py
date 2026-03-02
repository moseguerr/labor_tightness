
import glob
import pandas as pd
import numpy as np
import re
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import gc



def process_single_year(main_path, year):
    
    # Set threading limits to prevent excessive CPU use
    os.environ["OMP_NUM_THREADS"] = "3"
    os.environ["MKL_NUM_THREADS"] = "3"
    os.environ["NUMEXPR_NUM_THREADS"] = "3"
    
    # 🔹 Define the folder where the Parquet files are located
    input_path = os.path.join(main_path, year)
    
    # Define the columns used for grouping
    groupby_cols = [
        'gvkey', 'tic', 'cusip', 'comCounty', 'comDom', 'comCountry', 'comNAICS', 'comHeadquarters', 
        'OccFam', 'OccFamName', 'SOC', 'SOCName', 'CanonEmployer', 'Sector', 'SectorName', 
        'NAICS3', 'State', 'County', 
        'FIPSState', 'FIPSCounty', 'FIPS', 'BestFitMSA', 'BestFitMSAName', 'Year', 'qtr']
    
    # 🔹 Get all Parquet files in the specified folder
    file_list = sorted(glob.glob(os.path.join(input_path, "Main_*.parquet")))
    
    # 🔹 Extract the year from the first file (assuming all files belong to the same year)
    year = os.path.basename(file_list[0]).split("_")[1][:4]  # Extract YYYY from "Main_2010-01.parquet"
    
    # Create an empty DataFrame to store yearly data
    df_yearly = pd.DataFrame()
    
    
    # Process files in groups of 3 (quarterly)
    for i in range(0, len(file_list), 3):
        quarter_files = file_list[i:i+3]  # Take 3 files at a time
        
        groupby_cols = ['gvkey', 'tic', 'cusip', 'comCounty', 'comDom', 'comCountry', 'comNAICS', 'comHeadquarters', 
        'OccFam', 'OccFamName', 'SOC', 'SOCName', 'CanonEmployer', 'Sector', 'SectorName', 
        'NAICS3', 'State', 'County', 
        'FIPSState', 'FIPSCounty', 'FIPS', 'BestFitMSA', 'BestFitMSAName', 'Year', 'qtr']
        
        # Read and concatenate 3 months of data
        df_quarter = pd.concat([pd.read_parquet(file) for file in quarter_files], ignore_index=True)
        df_quarter.drop(columns=['BGTJobId'], errors='ignore', inplace=True)
        df_quarter.rename(columns={'Openingstotal_employer':'opEmptot_count'}, errors='ignore', inplace=True)
        
        # Convert '-999' back to NaN before aggregation
        numeric_cols = [col for col in df_quarter.columns if col not in groupby_cols]
    
        # Identify sum and mean columns
        count_cols = [col for col in numeric_cols if col.endswith('_count')]
        
        df_quarter[count_cols] = df_quarter.groupby(['CanonEmployer', 'FIPSState','BestFitMSA', 'FIPS', 'Sector', 'NAICS3','OccFam','SOC', 'qtr'])[count_cols].transform('sum')
    
        # Aggregate by quarter
        df_quarter = df_quarter.groupby(groupby_cols).mean().reset_index()
        
        #Variables by quarter
        df_quarter['sr_jobs']=df_quarter['sr_count']/df_quarter['opEmptot_count']
        df_quarter['main_jobs']=df_quarter['main_count']/df_quarter['opEmptot_count']
        df_quarter['sr_ind'] = (df_quarter['sr_count'] > 1).astype(int)
        df_quarter['main_ind'] = (df_quarter['main_count'] > 1).astype(int)
    
        df_quarter.drop(columns=['Month'], errors='ignore', inplace=True)
    
        # Append to yearly dataframe
        df_yearly = pd.concat([df_yearly, df_quarter], ignore_index=True)
        del df_quarter
        gc.collect()
        
    # Save the yearly dataset
    output_path=os.path.join(input_path, f"Aggregated_{year}.parquet")
    df_yearly.to_parquet(output_path , engine="pyarrow", compression='zstd', index=False)
    del df_yearly
    gc.collect()
    print(f"✅ Saved: Aggregated_{year}.parquet")
    
def process_wrapper(year):
    process_single_year(main_path, year)

if __name__ == "__main__":
    # Define the years and directories
    years = [str(year) for year in range(2010, 2023)]
    main_path = '/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'
    # ✅ Parallelize execution across years
    max_workers = 4  # Adjust based on available CPU cores
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_wrapper, years)

