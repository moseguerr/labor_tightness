#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 22:34:35 2024

@author: mgor
"""

import pandas as pd
import numpy as np
import re
import os

year='2010'
directory='/global/home/pc_moseguera/data/other_data/'
main_directory='/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Main/'
output_directory = f'/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/{year}/'


def process_files_for_year(year, main_directory, output_directory):
    """
    Processes all files in the specified directory for the given year
    and saves them as Parquet files in the output directory.

    Parameters:
        year (str): The year to process.
        main_directory (str): Path to the directory containing input files.
        output_directory (str): Path to the directory to save output files.
    """
    # Input directory for the specified year
    input_path = os.path.join(main_directory, year)
    
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    # List all files in the input directory
    files = [f for f in os.listdir(input_path) if f.endswith('.zip')]
    
    for i, file_name in enumerate(files, start=1):
        # Full path to the input file
        input_file_path = os.path.join(input_path, file_name)
        
        # Read the file
        df = pd.read_table(input_file_path, encoding='latin')
        

        #1. First Clean
        #########################
        # List of columns to drop
        columns_to_drop = [
            "Edu", "MaxEdu", "MaxDegree", "MinHrlySalary", "MaxHrlySalary", 
            "MaxExp", "Lat", "Lon", "CleanTitle", "BGTOcc", "TaxTerm", 
            "PayFrequency","JobDate","MSA"]
        
        # Create date
        df['Year'] = df['JobDate'].str[:4].astype(int)  
        df['Month'] = df['JobDate'].str[5:7].astype(int)  
        
        # Drop columns from the DataFrame
        df = df.drop(columns=columns_to_drop, errors="ignore")
        df['BestFitMSA']=pd.to_numeric(df['BestFitMSA'], errors='coerce').fillna(-999).astype(int)
        df['FIPSCounty']=pd.to_numeric(df['FIPSCounty'], errors='coerce').fillna(-999).astype(int)
        df['FIPS']=pd.to_numeric(df['FIPS'], errors='coerce').fillna(-999).astype(int)
        df = df.loc[df['OccFamName'] != 'na']
        df['SOCName'] = df['SOCName'].str.strip()
        df.loc[df['NAICS6'] == -999, 'NAICS6'] = 0
        df['Sector'] = pd.to_numeric(df['Sector'], errors='coerce').fillna(0).astype(int)
        del columns_to_drop
        
        # Rename the column 'employer' to 'CanonEmployer'
        df = df.rename(columns={"Employer": "CanonEmployer"})
        df= df[(df['CanonEmployer'].notna()) & (df['CanonEmployer'] != None) & (df['CanonEmployer'] != "None")]
        df = df.loc[df['CanonEmployer'] != 'na']
        
        #2. Data Transformation
        ################################################################
        #Largest Employer within ONET and MSA and ONET occupation growth
        # Step 1: Count the number of openings for each employer in each ONET group
        df['ONET_employer_openings'] = df.groupby(['ONET', 'CanonEmployer','BestFitMSA'])['ONET'].transform('count')
        # Step 2: Calculate the top decile threshold for each ONET group
        df['TopFiveThreshold'] = df.groupby(['ONET', 'BestFitMSA'])['ONET_employer_openings'].transform(lambda x: x.quantile(0.95))
        # Step 3: Assign 1 to employers in the top decile, 0 otherwise
        df['TopFiveEmpONETMSA'] = (df['ONET_employer_openings'] >= df['TopFiveThreshold']).astype(int)
        # Step 4: Drop the intermediate 'TopFivePercentThreshold' column if not needed
        df.drop(columns=['TopFiveThreshold'], inplace=True)
        # Step 5: Count the number of openings for each employer in each ONET group
        df['ONET_employer_openings'] = df.groupby(['ONET', 'CanonEmployer'])['ONET'].transform('count')
        # Step 6: Calculate the top decile threshold for each ONET group
        df['TopFiveThreshold'] = df.groupby(['ONET'])['ONET_employer_openings'].transform(lambda x: x.quantile(0.95))
        # Step 7: Assign 1 to employers in the top decile, 0 otherwise
        df['TopFiveEmpONET'] = (df['ONET_employer_openings'] >= df['TopFiveThreshold']).astype(int)
        # Step 8: Count the number of openings for each ONET group
        df['ONETMSAopenings'] = df.groupby(['ONET','BestFitMSA'])['ONET'].transform('count')
        df['ONETopenings'] = df.groupby(['ONET'])['ONET'].transform('count')
        # Step 9: Drop the columns if not needed
        df.drop(columns=['TopFiveThreshold','ONET_employer_openings'], inplace=True)
        
        #Wages information
        # Step 1: Create a column `NoWage` that takes the value 1 if either `MinSalary` or `MaxSalary` is -999
        df['NoWage'] = np.where((df['MinSalary'] == -999) & (df['MaxSalary'] == -999), 1, 0)
        # Step 2: Create `MeanWage` and set to NaN if `NoWage == 1`
        df['MeanWage'] = np.where(df['NoWage'] == 1, np.nan, (df['MinSalary'] + df['MaxSalary']) / 2)
        # Step 3: Create `VarRange` and set to NaN if `NoWage == 1`
        df['VarRange'] = np.where(df['NoWage'] == 1, np.nan, (df['MaxSalary'] - df['MinSalary']))
        # Drop wage columns
        df = df.drop(columns=['MinSalary', 'MaxSalary'], errors="ignore")
        
        
        #3. External Labor Data
        ########################
        #3.1 JOLTS
        # Directory containing the files
        
        file_national = directory + 'JOLTS/Nationalb.xlsx'
        file_state = directory + 'JOLTS/State.xlsx'
        
        df_jolts = pd.read_excel(file_national)
        df = pd.merge(df, df_jolts, on=['Year', 'Month'], how='left')
        del df_jolts
        
        df_jolts = pd.read_excel(file_state)
        df = pd.merge(
            df, df_jolts, on=['FIPSState','Year', 'Month'], how='left')
        del df_jolts
        del file_national
        del file_state
        
        #3.2 OESM
        # Check if the DataFrame contains the year 2010
        if (df['Year'] == 2010).any():
            print("Processing for Year 2010...")
        
            # State-level processing
            df_oesm = pd.read_excel(directory + 'OESM/state_M2010_dlb.xls')
            # First merge
            df_merge = pd.merge(df, df_oesm.drop(columns=['SOCName', 'GROUP']).drop_duplicates(subset=['FIPSState', 'SOC']), on=['FIPSState', 'SOC'], how='left', indicator=True)
            # Second merge
            col_to_drop=['totemp_st', 'empprse_st',
               'jobs1000_st', 'loc quotient_st', 'hmean_st', 'amean_st', 'meanprse_st',
               'hpct10_st', 'hpct25_st', 'hmedian_st', 'hpct75_st', 'hpct90_st',
               'apct10_st', 'apct25_st', 'amedian_st', 'apct75_st', 'apct90_st']
            differences = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=col_to_drop)
            df_merge2 = pd.merge(differences, df_oesm.drop(columns=['SOC', 'GROUP']).drop_duplicates(subset=['FIPSState', 'SOCName']), on=['FIPSState', 'SOCName'], how='left', indicator=True)
            # Third merge
            differences = df_merge2[df_merge2['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=col_to_drop)
            df_oesm = df_oesm[df_oesm['GROUP'] == 'major']
            df_oesm['OccFam'] = df_oesm['SOC'].str[:2]
            df_merge3 = pd.merge(differences, df_oesm.drop(columns=['SOC', 'SOCName', 'GROUP']), on=['FIPSState', 'OccFam'], how='left', indicator=True)
        
            # Combine results
            df = pd.concat([df_merge2[df_merge2['_merge'] != 'left_only'], df_merge3.drop(columns=['_merge'])], ignore_index=True)
            df = pd.concat([df_merge[df_merge['_merge'] != 'left_only'], df], ignore_index=True)
            df = df.drop(columns=['_merge'])
            del df_oesm, col_to_drop
        
            # MSA-level processing
            df_oesm = pd.read_csv(directory + 'OESM/ALL_2010.csv', delimiter=',')
            # First merge
            df_merge = pd.merge(df, df_oesm.drop(columns=['SOC', 'GROUP', 'FIPSState', 'BestFitMSAName']).drop_duplicates(subset=['BestFitMSA', 'SOCName']), on=['BestFitMSA', 'SOCName'], how='left', indicator=True)
            # Second merge
            differences = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=[col for col in differences.columns if col.endswith('_msa')])
            df_merge2 = pd.merge(differences, df_oesm.drop(columns=['SOCName', 'GROUP', 'FIPSState', 'BestFitMSAName']).drop_duplicates(subset=['BestFitMSA', 'SOC']), on=['BestFitMSA', 'SOC'], how='left', indicator=True)
            # Third merge
            differences = df_merge2[df_merge2['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=[col for col in differences.columns if col.endswith('_msa')])
            df_oesm = df_oesm[df_oesm['GROUP'] == 'major']
            df_oesm['OccFam'] = df_oesm['SOC'].str[:2]
            df_merge3 = pd.merge(differences, df_oesm.drop(columns=['SOC', 'SOCName', 'BestFitMSAName', 'FIPSState', 'GROUP']), on=['BestFitMSA', 'OccFam'], how='left', indicator=True)
        
            # Combine results
            df = pd.concat([df_merge2[df_merge2['_merge'] != 'left_only'], df_merge3.drop(columns=['_merge'])], ignore_index=True)
            df = pd.concat([df_merge[df_merge['_merge'] != 'left_only'], df], ignore_index=True)
            df = df.drop(columns=['_merge'])
            del df_oesm
        
            # National-level processing
            df_oesm = pd.read_excel(directory + 'OESM/national_M2010_dlb.xls')
            # First merge
            df_merge = pd.merge(df, df_oesm.drop(columns=['SOC', 'GROUP']).drop_duplicates(subset=['SOCName']), on=['SOCName'], how='left', indicator=True)
            # Second merge
            col_to_drop=['totemp_nt', 'empprse_nt', 'hmean_nt',
               'amean_nt', 'meanprse_nt', 'hpct10_nt', 'hpct25_nt', 'hmedian_nt',
               'hpct75_nt', 'hpct90_nt', 'apct10_nt', 'apct25_nt', 'amedian_nt',
               'apct75_nt', 'apct90_nt']
            differences = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=col_to_drop)
            df_merge2 = pd.merge(differences, df_oesm.drop(columns=['SOCName', 'GROUP']).drop_duplicates(subset=['SOC']), on=['SOC'], how='left', indicator=True)
            # Third merge
            differences = df_merge2[df_merge2['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
            differences = differences.drop(columns=col_to_drop)
            df_oesm = df_oesm[df_oesm['GROUP'] == 'major']
            df_oesm['OccFam'] = df_oesm['SOC'].str[:2]
            df_merge3 = pd.merge(differences, df_oesm.drop(columns=['SOC', 'SOCName', 'GROUP']), on=['OccFam'], how='left', indicator=True)
            del col_to_drop
            # Combine results
            df = pd.concat([df_merge2[df_merge2['_merge'] != 'left_only'], df_merge3.drop(columns=['_merge'])], ignore_index=True)
            df = pd.concat([df_merge[df_merge['_merge'] != 'left_only'], df], ignore_index=True)
            df = df.drop(columns=['_merge'])
            del df_oesm, df_merge2, df_merge3, df_merge
        
            print("Processing for Year 2010 completed.")
        else:
            print("Year 2010 not found. Skipping processing.")
        
        del differences
        
        # Check if any rows in df have Year > 2010
        if df['Year'].max() > 2010:
            
            # Extract the year
            year = str(df['Year'].max())
        
            # Load the corresponding parquet file
            df_oesm = pd.read_parquet(directory + 'OESM/other_years/' + year + '.parquet')
            columns_to_merge=['tot_emp',
               'emp_prse', 'jobs_1000', 'loc_quotient', 'pct_total',
               'h_mean', 'a_mean', 'mean_prse', 'h_pct10', 'h_pct25', 'h_median',
               'h_pct75', 'h_pct90', 'a_pct10', 'a_pct25', 'a_median', 'a_pct75',
               'a_pct90']
        
            # Define the base merge levels
            base_merge_levels = [
                ['NAICS6', 'SOCName'],
                ['NAICS6', 'SOC'],
                ['NAICS6', 'OccFam'],
                ['Sector', 'SOCName'],
                ['Sector', 'SOC'],
                ['Sector', 'OccFam'],
                ['SOCName'],
                ['SOC'],
                ['OccFam'],
                ['Sector'],
            ]
        
            # Define area-specific configurations
            area_config = {
                1: {"suffix": "_nt", "filter_condition": (df_oesm['AreaType'] == 1), "extra_key": []},
                2: {"suffix": "_st", "filter_condition": (df_oesm['AreaType'] > 1) & (df_oesm['AreaType'] < 4), "extra_key": ['FIPSState']},
                3: {"suffix": "_msa", "filter_condition": (df_oesm['AreaType'] > 3) & (df_oesm['AreaType'] < 6), "extra_key": ['BestFitMSA']},
            }
        
            # Initialize separate DataFrames for each area
            df_nt, df_st, df_msa = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
            # Process each AreaType
            for area_type, config in area_config.items():
                # Filter the DataFrame for the current AreaType based on the condition
                df_area = df_oesm[config["filter_condition"]].copy()
                suffix = config["suffix"]
                extra_key = config["extra_key"]
        
                # Generate merge levels dynamically by adding the extra key
                merge_levels = [extra_key + level for level in base_merge_levels]
        
                # Initialize DataFrames for successful merges and unmatched rows
                successful_merges = pd.DataFrame()
                unmatched = df.copy()
        
                # Perform iterative merging for the current AreaType
                for keys in merge_levels:
                    if unmatched.empty:
                        break  # Stop if all rows are successfully merged
        
                    # Prepare the subset of df_area for merging
                    area_subset = df_area[keys + columns_to_merge].drop_duplicates(subset=keys + extra_key , keep='first')
        
                    # Merge unmatched rows with the current level
                    df_merge = pd.merge(
                        unmatched,
                        area_subset,
                        on=keys,
                        how='left',
                        indicator=True,
                    )
        
                    # Append successfully merged rows
                    successful_merges = pd.concat([successful_merges, df_merge[df_merge['_merge'] != 'left_only']], ignore_index=True)
        
                    # Update unmatched rows for the next iteration
                    unmatched = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=columns_to_merge + ['_merge'], errors='ignore')
        
                # Include unmatched rows in the successful merges
                successful_merges = pd.concat([successful_merges, unmatched], ignore_index=True)
        
                # Rename merged columns to include the area-specific suffix
                successful_merges.rename(
                    columns=lambda x: x.lower().replace('_', '') + suffix if x in columns_to_merge else x,
                    inplace=True
                )
        
                # Drop the merge indicator column
                if '_merge' in successful_merges.columns:
                    successful_merges = successful_merges.drop(columns=['_merge'])
        
                # Assign the results to the appropriate DataFrame
                if area_type == 1:
                    df_nt = successful_merges
                elif area_type == 2:
                    df_st = successful_merges
                elif area_type == 3:
                    df_msa = successful_merges
        
            # Clean up the `_st` and `_msa` DataFrames
            df_st = df_st[['BGTJobId'] + [col for col in df_st.columns if col.endswith('_st')]]
            df_msa = df_msa[['BGTJobId'] + [col for col in df_msa.columns if col.endswith('_msa')]]
        
            # Merge the `_nt` DataFrame with `_st` and `_msa`
            df = pd.merge(df_nt, df_st, on='BGTJobId', how='left')
            df = pd.merge(df, df_msa, on='BGTJobId', how='left')
            del df_st, df_msa, df_nt, df_oesm
        
        else:
            print("No rows with Year > 2010. Skipping this section.")
        
        
        #3.3 Economic Profile 
        #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/Economic Profile/'
        df_cainc = pd.read_csv(directory + 'Economic_Profile/ALL_CAINC.csv', delimiter=',', encoding='latin')
        df_cainc = df_cainc[df_cainc['Year'] == df['Year'].unique()[0]]
        
        # Filter the national-level data from df_cainc
        df_nt = df_cainc[(df_cainc['FIPS'] == 0) & (df_cainc['FIPSState'] == 0) & (df_cainc['FIPSCounty'] == 0)]
        
        # Add suffix '_nt' to non-key columns in df_nt
        columns_to_merge = [col for col in df_nt.columns if col not in ['FIPS', 'FIPSState', 'FIPSCounty', 'Year']]
        df_nt = df_nt[columns_to_merge].add_suffix('_nt')
        
        # Extract the row of national values as a dictionary
        national_values = df_nt.iloc[0].to_dict()
        
        # Add these values as new columns to df
        for key, value in national_values.items():
            df[key] = value
        
        # Filter state and county-level data from df_cainc
        
        merge_config = {
            "state": {
                "suffix": "_st",
                "filter_condition": (df_cainc['FIPSCounty'] == 0) & (df_cainc['FIPSState'] != 0),
                "merge_key": ['FIPSState'],
                "extra_key": ['FIPS', 'FIPSCounty', 'Year']
            },
            "county": {
                "suffix": "_ct",
                "filter_condition": (df_cainc['FIPSCounty'] != 0),
                "merge_key": ['FIPS'],
                "extra_key": ['FIPSState', 'FIPSCounty', 'Year']
            }
        }
        
        # Process each level
        for level, config in merge_config.items():
            # Filter the subset of df_cainc based on the condition
            df_level = df_cainc[config['filter_condition']].copy()
            suffix = config["suffix"]
            merge_keys = config["merge_key"]
            extra_key = config["extra_key"]
            df_level=df_level[merge_keys + columns_to_merge].drop_duplicates(subset=merge_keys, keep='first')
        
            # Rename columns to include the area-specific suffix
            df_level.rename(
                columns=lambda x: x + suffix if x in columns_to_merge else x,
                inplace=True
            )
            
            
            # Perform the merge without dropping keys prematurely
            df_aux = pd.merge(
                df,
                df_level,
                on=merge_keys,
                how='left'
            )
            
         # Assign the results to the appropriate DataFrame
            if level == 'state':
                df_st = df_aux
            elif level == 'county':
                df_ct = df_aux
        
        # Clean up the `_st` and `_ct` DataFrames
        # Construct the '_st' columns dynamically
        st_columns = [col + '_st' for col in columns_to_merge]
        ct_columns = [col + '_ct' for col in columns_to_merge]
        
        df_st = df_st[['BGTJobId'] + st_columns]
        df_ct = df_ct[['BGTJobId'] + ct_columns]
        
        # Merge the `_nt` DataFrame with `_st` and `_msa`
        df = pd.merge(df, df_st, on='BGTJobId', how='left')
        df = pd.merge(df, df_ct, on='BGTJobId', how='left')
        del df_aux, df_nt, df_st, df_ct, df_level, key, config, columns_to_merge, df_cainc, extra_key, level, merge_keys, national_values, st_columns, suffix, value, ct_columns, merge_config
        
        #3.4 GDP
        #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/GDP/'
        df_cagdp = pd.read_csv(directory + 'GDP/ALL_CAGDP.csv', delimiter=',', encoding='latin')
        df_cagdp = df_cagdp[df_cagdp['Year'] == df['Year'].unique()[0]]
        indicator_columns= ['FIPS', 'FIPSState', 'FIPSCounty', 'Year', 'Sector', 'SectorName']
        columns_to_merge = [col for col in df_cagdp.columns if col not in indicator_columns ]
        
        
        merge_config = {
            "national": {
                "suffix": "_nt",
                "filter_condition": (df_cagdp['FIPS'] == 0) & (df_cagdp['FIPSState'] == 0) & (df_cagdp['FIPSCounty'] == 0),
                "merge_key": ['Sector'],
            },
            "state": {
                "suffix": "_st",
                "filter_condition": (df_cagdp['FIPSCounty'] == 0) & (df_cagdp['FIPSState'] != 0),
                "merge_key": ['FIPSState','Sector'],
            },
            "county": {
                "suffix": "_ct",
                "filter_condition": (df_cagdp['FIPSCounty'] != 0),
                "merge_key": ['FIPS','Sector'],
            }
        }
        
        # Process each level
        for level, config in merge_config.items():
            # Filter the subset of df_cagdp based on the condition
            df_level = df_cagdp[config['filter_condition']].copy()
            suffix = config["suffix"]
            merge_key = config["merge_key"]
            df_level=df_level[merge_key + columns_to_merge].drop_duplicates(subset=merge_key, keep='first')
        
            # Rename columns to include the area-specific suffix
            df_level.rename(
                columns=lambda x: x + suffix if x in columns_to_merge else x,
                inplace=True
            )
            
            
            # Perform the merge without dropping keys prematurely
            df_aux = pd.merge(
                df,
                df_level,
                on=merge_key,
                how='left'
            )
            
         # Assign the results to the appropriate DataFrame
            if level == 'national':
                df_nt = df_aux
            elif level == 'state':
                df_st = df_aux
            elif level == 'county':
                df_ct = df_aux
        
        # Clean up the `_st` and `_msa` DataFrames
        df_nt = df_nt[['BGTJobId','gdp_nt']]
        df_st = df_st[['BGTJobId', 'gdp_st']]
        df_ct = df_ct[['BGTJobId','gdp_ct']]
        
        # Merge the `_nt` DataFrame with `_st` and `_msa`
        df= pd.merge(df, df_nt, on='BGTJobId', how='left')
        df= pd.merge(df, df_st, on='BGTJobId', how='left')
        df= pd.merge(df, df_ct, on='BGTJobId', how='left')
        del df_aux, df_nt, df_st, df_ct, df_level, columns_to_merge, config, df_cagdp, indicator_columns, level, merge_config, merge_key, suffix
        
        
        #3.5 Unionization
        df_msa = pd.read_csv(directory + 'Union/msas_union.csv')
        df_st = pd.read_csv(directory + 'Union/state_unionb.csv')
        df_nt = df_st[(df_st['FIPSState'] == 0) ]
        df_nt.rename(columns={'pctunion_st': 'pctunion_nt'}, inplace=True)
        df_ind=pd.read_csv(directory + 'Union/industry.csv')
        df_soc=pd.read_csv(directory + 'Union/soc_union.csv')
        
        df_union=pd.merge(df,df_msa.drop(columns=['BestFitMSAName']),on=['BestFitMSA','Year'],how='left', indicator=True)
        df_union=pd.merge(df_union.drop(columns=['_merge']),df_st,on=['FIPSState','Year'],how='left', indicator=True)
        df_union=pd.merge(df_union.drop(columns=['_merge']),df_nt.drop(columns=['FIPSState']),on=['Year'],how='left', indicator=True)
        
        # Define the merging levels and their hierarchy dynamically
        merge_hierarchy = ["Sector", "NAICS3", "NAICS4", "NAICS5", "NAICS6"]
        
        # Generate dynamic merge levels with conditions
        merge_levels = []
        for i, level in enumerate(merge_hierarchy):
            # Levels above the current level should be checked for -999
            higher_levels = merge_hierarchy[:i]
            # Levels below the current level will be dropped
            drop_levels = merge_hierarchy[i+1:]
        
            # Define the condition for filtering rows
            def condition(df, level=level, higher_levels=higher_levels):
                return (df[level] != -999) & (df[higher_levels].eq(-999).all(axis=1))
        
            # Append the merge configuration
            merge_levels.append({
                "level": level,
                "drop": drop_levels,
                "condition": condition
            })
        # Initialize the final merged DataFrame
        final_merge = pd.DataFrame()
        df_union=df_union.drop(columns=['_merge'], errors='ignore')
        # Iterate through each dynamic merge level
        for merge_config in merge_levels:
            level = merge_config["level"]
            drop_columns = merge_config["drop"]
            condition = merge_config["condition"]
        
            # Filter rows matching the current condition
            subset = df_union[condition(df_union)]
        
            # If no rows match the condition, skip this level
            if subset.empty:
                continue
        
            # Prepare the `df_ind` subset for the current level
            df_ind_subset = (
                df_ind[["Year", "pctunion_ind", level]]
                .dropna(subset=[level])
                .drop_duplicates(subset=["Year", level], keep="first")
            )
        
            # Perform the merge
            df_merge = pd.merge(
                subset,
                df_ind_subset.drop(columns=drop_columns, errors="ignore"),
                on=["Year", level],
                how="left"
            )
        
            # Append the successfully merged rows to the final DataFrame
            final_merge = pd.concat([final_merge, df_merge], ignore_index=True)
        
        
        df_union=final_merge
        df_union.OccFam=df_union.OccFam.astype(int)
        
        del final_merge
        
        # Define the merge columns and initialize variables
        merge_columns = ['SOC', 'SOCName', 'OccFam']
        final_merge = pd.DataFrame()
        unmatched = df_union.copy()
        
        # Loop through the merge hierarchy dynamically
        for merge_key in merge_columns:
            # Determine columns to drop dynamically
            drop_columns = ['OccFamName'] + [col for col in merge_columns if col != merge_key]
            
            # Perform the merge
            df_merge = pd.merge(
                unmatched.drop(columns=['pctunion_occ'], errors='ignore'),
                df_soc.drop(columns=drop_columns).drop_duplicates(subset=['Year', merge_key], keep="first"),
                on=['Year', merge_key],
                how="left",
                indicator=True
            )
        
            # Append successfully merged rows to the final DataFrame
            successful_merge = df_merge[df_merge['_merge'] != 'left_only']
            final_merge = pd.concat([final_merge, successful_merge], ignore_index=True)
        
            # Update unmatched rows for the next iteration
            unmatched = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge'], errors='ignore')
        
        # Combine any remaining unmatched rows to the final merge
        final_merge = pd.concat([final_merge, unmatched], ignore_index=True)
        
        # Final cleanup: Drop the merge indicator column if it exists
        final_merge = final_merge.drop(columns=['_merge'], errors='ignore')
        
        df=final_merge
        
        del final_merge, df_union, unmatched, successful_merge, df_ind, df_ind_subset, df_merge, 
        del df_msa, df_nt, df_soc, df_st, drop_columns, drop_levels, higher_levels, level
        del i, merge_columns, merge_config,merge_key, merge_levels, merge_hierarchy, subset
        
        df.OccFam=df.OccFam.astype(str)
        
        
        ##3.6 LAUS
        #State 
        df_aux=pd.read_csv(directory + 'LAUS/LAUS_state.csv', delimiter=',') 
        df=pd.merge(df, df_aux, on=['FIPSState', 'Year','Month'], how='left')
        del df_aux
        
        #MSA
        df_LAUS=pd.read_csv(directory + 'LAUS/LAUS_msa.csv', delimiter=',') 
        df=pd.merge(df, df_LAUS.drop(columns=['FIPSState','BestFitMSAName_msa']), on=['BestFitMSA' ,'Year','Month'], how='left')
        del df_LAUS
        
        #County
        df_county=pd.read_csv(directory + 'LAUS/LAUS_ct.csv', delimiter=',') 
        df = pd.merge(
            df, df_county.drop(columns=['FIPSState','FIPSCounty']), on=['FIPS','Year', 'Month'], how='left'
        )
        del df_county
        
        #3.7 Demographic Composition
        def clean_soc_mapping(df):
        
            # Replace commas in the DataFrame
            df = df.replace(',', '', regex=True)
            
            # Clean 'SOCName' column
            df['SOCName'] = df['SOCName'].str.title()
            df['SOCName'] = df['SOCName'].replace('--', '-', regex=True)
            df['SOCName'] = df['SOCName'].str.replace(
                r'(?<=[-/])([a-z])', 
                lambda match: match.group(1).upper(),
                regex=True
            )
            
            # Strip whitespace from 'SOC' and 'SOCName'
            df['SOC'] = df['SOC'].str.strip()
            df['SOCName'] = df['SOCName'].str.strip()
            
            # Drop duplicates to ensure unique pairs
            df = df.drop_duplicates()
        
            
            return df
        df_dem=pd.read_csv(directory + 'Demographic_Composition/dem_occst.csv', delimiter=',') 
        # Apply the function to the column
        df = clean_soc_mapping(df)
        df_merge=pd.merge(
                    df, df_dem.drop(columns=['SOCName']).drop_duplicates(subset=['SOC','FIPSState','Year']), on=['SOC','FIPSState','Year'], how='left', indicator=True
                )
        difference=df_merge[df_merge['_merge']=='left_only']
        columns_to_drop=['Male','Female','white','black','americanIndian','alaskaNative','asian','hawaiianPacificIslander','someOtherRace','ageMean','_merge']
        df_merge2=pd.merge(
                    difference.drop(columns=columns_to_drop), df_dem.drop(columns=['SOC']).drop_duplicates(subset=['SOCName','FIPSState','Year']), on=['SOCName','FIPSState','Year'], how='left', indicator=True
                )
        df=pd.concat([df_merge[df_merge['_merge']=='both'].drop(columns=['_merge']), df_merge2.drop(columns=['_merge'])],ignore_index=True)
        del df_dem, df_merge, df_merge2
        
        df_race=pd.read_csv(directory + 'Demographic_Composition/dem_msa.csv', delimiter=',') 
        df=pd.merge(df, df_race, on=['Year','BestFitMSA'],how='left')
        del df_race
        
        #3.8 Labor Productivity
        df_prod=pd.read_csv(directory + 'Industry_Productivity/prod_ind.csv', delimiter=',') 
        df_prod = df_prod.loc[:, ~df_prod.columns.str.startswith('k')]
        df_prod.drop(columns=['NAICS6'], inplace=True)
        # Define the merging levels and their hierarchy dynamically
        merge_hierarchy = ["Sector", "NAICS3", "NAICS4", "NAICS5"]
        
        # Generate dynamic merge levels with conditions
        merge_levels = []
        for i, level in enumerate(merge_hierarchy):
            # Levels above the current level should be checked for -999
            higher_levels = merge_hierarchy[:i]
            # Levels below the current level will be dropped
            drop_levels = merge_hierarchy[i+1:]
        
            # Define the condition for filtering rows
            def condition(df, level=level, higher_levels=higher_levels):
                return (df[level] != -999) & (df[higher_levels].eq(-999).all(axis=1))
        
            # Append the merge configuration
            merge_levels.append({
                "level": level,
                "drop": drop_levels,
                "condition": condition
            })
        # Initialize the final merged DataFrame
        final_merge = pd.DataFrame()
        # Iterate through each dynamic merge level
        for merge_config in merge_levels:
            level = merge_config["level"]
            drop_columns = merge_config["drop"]
            condition = merge_config["condition"]
        
            # Filter rows matching the current condition
            subset = df[condition(df)]
        
            # If no rows match the condition, skip this level
            if subset.empty:
                continue
        
            # Prepare the `df_ind` subset for the current level
            df_prod_subset = (
                df_prod[["Year", "lProd", level]]
                .dropna(subset=[level])
                .drop_duplicates(subset=["Year", level], keep="first")
            )
        
            # Perform the merge
            df_merge = pd.merge(
                subset,
                df_prod_subset.drop(columns=drop_columns, errors="ignore"),
                on=["Year", level],
                how="left"
            )
        
            # Append the successfully merged rows to the final DataFrame
            final_merge = pd.concat([final_merge, df_merge], ignore_index=True)
        
        df=final_merge
        del final_merge
        
        #3.9 NGOs
        df_aux=pd.read_csv(directory + 'NGOs/ngos.csv', delimiter=',') 
        
        # Define a function to clean and normalize company names
        def clean_company_name(name):
            if pd.isna(name):
                return name
            
            # Dictionary to map variations of terms to their normalized form (only at the end)
            replacements = {
                r'\bcorp(oration)?\b$': '',  # Remove "Corp" or "Corporation" at the end
                r'\binc(orporated)?\b$': '',  # Remove "Inc" or "Incorporated" at the end
                r'\bltd\b$': '',  # Remove "LTD" at the end
                r'\bco(mpany)?\b$': '',  # Remove "Co" or "Company" at the end
                r'\bplc\b$': '',  # Remove "PLC" at the end
            }
            
            # Normalize the name
            normalized_name = name.lower()  # Convert to lowercase
            normalized_name = re.sub(r'[.,]', '', normalized_name)  # Remove commas and periods
            normalized_name = re.sub(r'[^a-zA-Z0-9 &\']+', '', normalized_name)  # Remove special characters except &, '
            normalized_name = re.sub(r'-', ' ', normalized_name)  # Replace hyphens with spaces
            
            # Apply replacements only at the end
            for pattern, replacement in replacements.items():
                normalized_name = re.sub(pattern, replacement, normalized_name)
            
            # Capitalize the first letter of each word, including those after '&', but not after an apostrophe
            words = normalized_name.split()
            capitalized_words = []
            for word in words:
                if "'" in word:
                    # Handle words with apostrophes: capitalize the first part, keep the rest as is
                    parts = word.split("'")
                    capitalized_words.append(parts[0].capitalize() + "'" + parts[1])
                else:
                    capitalized_words.append(word.capitalize())  # Capitalize all other words
            
            return ' '.join(capitalized_words).strip()  # Join words and remove leading/trailing whitespace
        
        # Apply the cleaning function to both DataFrames
        df['clean_company_name'] = df['CanonEmployer'].apply(clean_company_name)
        
        # Merge the two DataFrames using the cleaned company names
        df = pd.merge(
            df,
            df_aux.drop_duplicates(subset=['clean_company_name']),
            on='clean_company_name',
            how='left'
        )
        
        del df_aux, columns_to_drop, df_merge, df_prod, df_prod_subset, difference, drop_columns, drop_levels, higher_levels, i
        del level, merge_config, merge_hierarchy, merge_levels, subset
        
        #COMPUSTAT
        df_comp = pd.read_parquet(directory + 'COMPUSTAT/compustat_quarter.parquet')
        
        df=pd.merge(
            df,
            df_comp.drop_duplicates(subset=['clean_company_name','Year','Month']).drop(columns=['conm', 'conml']),
            on=['clean_company_name','Year','Month'],
            how='left'
        )
        
        del df_comp
        
        # Construct the output file name
        output_file_name = f"Main{i:02d}_{year}.parquet"
        output_file_path = os.path.join(output_directory, output_file_name)
        
        # Save to Parquet
        df.to_parquet(output_file_path, engine='pyarrow', index=False)
        print(f"Processed and saved: {output_file_path}")
