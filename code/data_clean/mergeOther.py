#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 15:48:27 2025

@author: mgor
"""


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
from concurrent.futures import ProcessPoolExecutor, as_completed
import gc

def process_files(input_file_path, output_directory):
    file_name = os.path.basename(input_file_path)
    # Read the file
    df = pd.read_table(input_file_path, encoding='latin')
    directory='/global/home/pc_moseguera/data/other_data/'
    
    #1. First Clean
    #########################
    # List of columns to drop
    columns_to_drop = [
        "Edu", "MaxEdu", "MaxDegree", "MinHrlySalary", "MaxHrlySalary", 
        "MaxExp", "Lat", "Lon", "CleanTitle", "BGTOcc", "TaxTerm", 
        "PayFrequency","JobDate","MSA","JobId",'CanonTitle',
        'BGTCareerAreaName2','MSAName','Internship', 'ONET',
         'ONETName','BGTOccName','BGTOccGroupName',
         'BGTOccGroupName2','BGTCareerAreaName','BGTCareerAreaName2',]
    
    # Create date
    df['Year'] = df['JobDate'].str[:4].astype(int)  
    df['Month'] = df['JobDate'].str[5:7].astype(int)  
    df['qtr'] = pd.cut(
    df['Month'],
    bins=[0, 3, 6, 9, 12],  # Define cut points (months)
    labels=[1, 2, 3, 4],     # Corresponding quarter values
    right=True               # Ensure inclusivity of upper bound
    ).astype(int)     
    
    #Drop Internships
    df = df.loc[df['Internship'] != 1]
    
    # Drop columns from the DataFrame
    df = df.drop(columns=columns_to_drop, errors="ignore")
    
    # Rename the column 'employer' to 'CanonEmployer'
    df = df.rename(columns={"Employer": "CanonEmployer"})
    df= df[(df['CanonEmployer'].notna()) & (df['CanonEmployer'] != None) & (df['CanonEmployer'] != "None")]
    df = df.loc[df['CanonEmployer'] != 'na'] 
    df["BGTJobId"] = pd.to_numeric(df["BGTJobId"], errors="coerce")
    df = df.dropna(subset=["BGTJobId"])
    df["BGTJobId"] = df["BGTJobId"].astype(int)
    df['BestFitMSA']=pd.to_numeric(df['BestFitMSA'], errors='coerce').fillna(-999).astype(int)
    df['FIPSCounty']=pd.to_numeric(df['FIPSCounty'], errors='coerce').fillna(-999).astype(int)
    df['FIPS']=pd.to_numeric(df['FIPS'], errors='coerce').fillna(-999).astype(int)
    df['FIPSState']=pd.to_numeric(df['FIPSState'], errors='coerce').fillna(-999).astype(int)
    df = df[(df['BestFitMSA'] != -999) & (df['FIPS'] != -999)]
    df = df.loc[df['Sector'] != 'na']
    df['OccFam'] = pd.to_numeric(df['OccFam'], errors='coerce').fillna(-999).astype(int)
    df = df.loc[df['OccFamName'] != -999]
    df['SOC'] = df['SOC'].replace('na', '-999')
    df['SOCName'] = df['SOCName'].str.strip()
    df.loc[df['NAICS6'] == -999, 'NAICS6'] = 0
    df['Sector'] = df.apply(lambda row: str(row['NAICS3'])[:2] if row['NAICS3'] != -999 else str(row['Sector'])[:2], axis=1)
    df['Sector'] = pd.to_numeric(df['Sector'], errors='coerce').fillna(-999).astype(int)
    df.loc[df['NAICS6'] == 0, 'NAICS6'] = -999
    del columns_to_drop
    
    #2. Data Transformation
    ################################################################
    #Largest Employer within SOC and MSA and SOC occupation growth
    # Step 1: Count the number of openings for each employer in each SOC/NAICS group
    df['SOC_employer_openings'] = df.groupby(['SOC', 'CanonEmployer','BestFitMSA'])['SOC'].transform('count')
    df['NAICS_employer_openings'] = df.groupby(['NAICS6', 'CanonEmployer','BestFitMSA'])['SOC'].transform('count')
    df['Sector_employer_openings'] = df.groupby(['NAICS6', 'CanonEmployer','BestFitMSA'])['SOC'].transform('count')

    # Step 2: Calculate the top decile threshold for each SOC group
    df['TopFiveThreshold'] = df.groupby(['SOC', 'BestFitMSA'])['SOC_employer_openings'].transform(lambda x: x.quantile(0.95))
    # Step 3: Assign 1 to employers in the top decile, 0 otherwise
    df['TopFiveEmpSOCMSA'] = (df['SOC_employer_openings'] >= df['TopFiveThreshold']).astype(int)
    # Step 4: Drop the intermediate 'TopFivePercentThreshold' column if not needed
    df.drop(columns=['TopFiveThreshold'], inplace=True)
    # Step 5: Count the number of openings for each employer in each SOC group
    df['SOC_employer_openings'] = df.groupby(['SOC', 'CanonEmployer'])['SOC'].transform('count')
    # Step 6: Calculate the top decile threshold for each SOC group
    df['TopFiveThreshold'] = df.groupby(['SOC'])['SOC_employer_openings'].transform(lambda x: x.quantile(0.95))
    # Step 7: Assign 1 to employers in the top decile, 0 otherwise
    df['TopFiveEmpSOC'] = (df['SOC_employer_openings'] >= df['TopFiveThreshold']).astype(int)
    # Step 8: Count the number of openings for each SOC group
    df['SOCFIPSopenings'] = df.groupby(['SOC','FIPS'])['SOC'].transform('count')
    df['SOCMSAopenings'] = df.groupby(['SOC','BestFitMSA'])['SOC'].transform('count')
    df['SOCopenings'] = df.groupby(['SOC'])['SOC'].transform('count')
    # Step 9: Drop the columns if not needed
    df.drop(columns=['TopFiveThreshold','SOC_employer_openings'], inplace=True)
    
    # Step 2: Calculate the top decile threshold for each NAICS group
    df['TopFiveThreshold'] = df.groupby(['NAICS6', 'BestFitMSA'])['NAICS_employer_openings'].transform(lambda x: x.quantile(0.95))
    # Step 3: Assign 1 to employers in the top decile, 0 otherwise
    df['TopFiveEmpNAICSMSA'] = (df['NAICS_employer_openings'] >= df['TopFiveThreshold']).astype(int)
    # Step 4: Drop the intermediate 'TopFivePercentThreshold' column if not needed
    df.drop(columns=['TopFiveThreshold'], inplace=True)
    # Step 5: Count the number of openings for each employer in each NAICS6 group
    df['NAICS_employer_openings'] = df.groupby(['NAICS6', 'CanonEmployer'])['NAICS6'].transform('count')
    # Step 6: Calculate the top decile threshold for each NAICS6 group
    df['TopFiveThreshold'] = df.groupby(['NAICS6'])['NAICS_employer_openings'].transform(lambda x: x.quantile(0.95))
    # Step 7: Assign 1 to employers in the top decile, 0 otherwise
    df['TopFiveEmpNAICS'] = (df['NAICS_employer_openings'] >= df['TopFiveThreshold']).astype(int)
    # Step 8: Count the number of openings for each NAICS6 group
    df['NAICSMSAopenings'] = df.groupby(['NAICS6','BestFitMSA'])['NAICS6'].transform('count')
    df['NAICSFIPSopenings'] = df.groupby(['NAICS6','FIPS'])['SOC'].transform('count')
    df['NAICSopenings'] = df.groupby(['NAICS6'])['NAICS6'].transform('count')
    # Step 9: Drop the columns if not needed
    df.drop(columns=['TopFiveThreshold','NAICS_employer_openings'], inplace=True)
    
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

    # Extract the year
    year = str(df['Year'].max())

    # Load the corresponding parquet file
    df_oesm = pd.read_parquet(directory + 'OESM/' + year + '.parquet')
    rename_columns = {'loc_q': 'loc_quotient', 'pct_tot': 'pct_total', 'jobs_1000_orig':'jobs_1000'}
    df_oesm = df_oesm.rename(columns={k: v for k, v in rename_columns.items() if k in df_oesm.columns})
    df_oesm.drop(columns=['loc_quotient','pct_total', 'pct_rpt','prim_state', 'i_group','o_group','GROUP','group'], inplace=True, errors='ignore')
    df_oesm['FIPS']=df_oesm['BestFitMSA']
    
    # Define merge strategies
    merge_strategies = [
        ['FIPSState', 'BestFitMSA', 'SOC','OccFam'],
        ['FIPSState', 'BestFitMSA', 'SOCName','OccFam'],
        ['FIPSState', 'FIPS', 'SOC', 'OccFam']
    ]
    
    # Initialize list for merged data & DataFrame to track unmatched rows
    merged_parts = []
    remaining_df = df.copy()  # Start with the full dataset
    
    for keys in merge_strategies:
        # Fix column renaming issue (rename _x back to original)
        for col in keys:
            if f"{col}_x" in remaining_df.columns:
                remaining_df.rename(columns={f"{col}_x": col}, inplace=True)
            if f"{col}_y" in remaining_df.columns:
                remaining_df.rename(columns={f"{col}_y": col}, inplace=True)
    
        # Ensure all merge keys exist in both DataFrames before merging
        valid_keys = all(key in remaining_df.columns for key in keys) and \
                     all(key in df_oesm.columns for key in keys)
    
        if not valid_keys:
            print(f"⚠️ Skipping merge for keys: {keys} (missing columns)")
            continue
    
        print(f"🔄 Trying merge on keys: {keys}...")
    
        # Perform merge with explicit suffixes to avoid confusion
        df_merged = remaining_df.merge(df_oesm.drop_duplicates(subset=keys).drop(columns=['_merge'], errors='ignore'), on=keys, how='left', indicator=True, suffixes=('', '_drop'))
    
        # Drop duplicate columns that were renamed (suffix _drop)
        df_merged.drop(columns=[col for col in df_merged.columns if col.endswith('_drop')], errors='ignore', inplace=True)
    
        # Separate matched & unmatched rows
        matched_rows = df_merged[df_merged['_merge'] == 'both'].drop(columns=['_merge'])
        unmatched_rows = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])
    
        # Store successfully merged part
        merged_parts.append(matched_rows)
    
        # Update remaining_df to only the unmatched rows
        remaining_df = unmatched_rows.copy()
    
        # If all rows are merged, stop early
        if remaining_df.empty:
            print("✅ All rows successfully merged. Exiting early.")
            break
    
    # Concatenate all merged parts into a final DataFrame
    df = pd.concat(merged_parts + [remaining_df], ignore_index=True)
    del df_oesm, remaining_df, merged_parts, matched_rows
    gc.collect()
    print(f"✅ Merging complete! Final DataFrame shape: {df.shape}")

    #Industry Employment
    # Load the corresponding parquet file
    df_ind = pd.read_parquet(directory + 'Industry Employment/' + year + '.parquet')
    df['BestFitMSA4'] = pd.to_numeric(df['BestFitMSA'].astype(str).str[:4], errors='coerce').fillna(-999).astype(int)
    df_ind = df_ind[df_ind['qtr'] == df['qtr'].iloc[0]]
    df_ind.drop(columns=['Year', 'qtr'], inplace=True, errors='ignore')
    df = pd.merge(df, df_ind[df_ind['BestFitMSA4']!=-999].drop(columns=['FIPS', 'FIPSState', 'FIPSCounty']), on=['Sector', 'NAICS3', 'BestFitMSA4'], how='left', indicator=True)
    unmatched = df[df['_merge'] == 'left_only'].drop(columns=['_merge','shiftNAICS', '07LNAICSShare',
       'BShareimq', 'BShareHK','wkWageNAICS'], errors='ignore')
    # Step 4: Second merge using FIPSState & FIPSCounty
    df_aux = pd.merge(
        unmatched,
        df_ind.drop(columns=['BestFitMSA4', 'FIPS'], errors='ignore'),
        on=[ 'Sector', 'NAICS3', 'FIPSState', 'FIPSCounty'],
        how='left'
    )
    # Step 5: Concatenate successfully merged data
    df = pd.concat([
    df[df['_merge'] != 'left_only'],  # Keep the successfully merged ones from first merge
    df_aux.drop(columns=['_merge'], errors='ignore')  # Append the successfully merged from second merge
    ], ignore_index=True)
    del df_aux, df_ind
    df.drop(columns=['BestFitMSA4'], inplace=True, errors='ignore')
    gc.collect
    
    #3.3 Economic Profile 
    #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/Economic Profile/'
    df_cainc = pd.read_csv(directory + 'Economic_Profile/ALL_CAINC.csv', delimiter=',', encoding='latin')
    df_cainc = df_cainc[df_cainc['Year'] == df['Year'].unique()[0]]
    df=pd.merge(df,df_cainc, on=['FIPS', 'FIPSState', 'FIPSCounty', 'Year'],how='left')
    del df_cainc
    gc.collect()
 
    #3.4 GDP
    #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/GDP/'
    df_cagdp = pd.read_csv(directory + 'GDP/ALL_CAGDP.csv', delimiter=',', encoding='latin')
    df_cagdp = df_cagdp[df_cagdp['Year'] == df['Year'].unique()[0]]
    df=pd.merge(df,df_cagdp, on=['FIPSState', 'FIPSCounty','Sector'], how='left')
    
    #By industry-quarter + crisis
    df_ind = pd.read_parquet(directory + 'Industry_Productivity/gdpchange_quarter.parquet')
    df=pd.merge(df, df_ind, on=['NAICS3','Sector','Year','Month'], how='left')
    del df_ind
    df_crisis = pd.read_parquet(directory + 'Industry_Productivity/gdp_crisis.parquet')
    df=pd.merge(df, df_crisis, on=['NAICS3','Sector','Month'], how='left')
    del df_crisis

    #3.5 Unionization
    df_loc = pd.read_csv(directory + 'Union/loc_union.csv')
    df_ind=pd.read_csv(directory + 'Union/industry.csv')
    df_soc=pd.read_csv(directory + 'Union/soc_union.csv')
    
    df_loc=pd.read_csv(directory + '/loc_union.csv')

    df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_loc[df_loc['BestFitMSA']!=-999].drop(columns=['FIPSState'], errors='ignore'), on=['Year', 'BestFitMSA'], how='left', indicator=True)
    unmatched = df[df['_merge'] == 'left_only'].drop(columns=['_merge','lpctunion'], errors='ignore')
    # Step 4: Second merge using FIPSState & FIPSCounty
    df_aux = pd.merge(
        unmatched,
        df_loc[df_loc['BestFitMSA']==-999].drop(columns=['BestFitMSA'], errors='ignore'),
        on=[ 'Year', 'FIPSState'],
        how='left', indicator=True
    )
    df = pd.concat([
        df[df['_merge'] != 'left_only'],  # Keep the successfully merged ones from first merge
        df_aux.drop(columns=['_merge'], errors='ignore')  # Append the successfully merged from second merge
    ], ignore_index=True)
    del df_loc, df_aux
    
    df_ind=pd.read_csv(directory + '/industry.csv')
    df=pd.merge(df,df_ind.drop_duplicates(subset=['Year', 'Sector', 'NAICS3', 'NAICS4', 'NAICS5',
           'NAICS6']) , on=['Year', 'Sector', 'NAICS3', 'NAICS4', 'NAICS5',
       'NAICS6'],how='left', indicator=True)

    del df_ind
    df_soc=pd.read_csv(directory + 'Union/soc_union.csv')
    df_aux=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_soc[df_soc['SOC']!='-999'].drop(columns=['OccFam','OccFamName','SOCName'],
                                errors='ignore').drop_duplicates(subset=['Year','SOC']), 
                                on=['Year', 'SOC'], how='left', indicator=True)
    unmatched = df_aux[df_aux['_merge'] == 'left_only'].drop(columns=['_merge','pctunion_occ'], errors='ignore')
    df_aux2 = pd.merge(
        unmatched,
        df_soc[df_soc['SOC']!='-999'].drop(columns=['OccFam','OccFamName','SOC'],
                                errors='ignore').drop_duplicates(subset=['Year','SOCName']), 
                                on=['Year', 'SOCName'], how='left', indicator=True)
    unmatched = df_aux2[df_aux2['_merge'] == 'left_only'].drop(columns=['_merge','pctunion_occ'], errors='ignore')
    df_aux3 = pd.merge(
        unmatched,
        df_soc[df_soc['SOC']=='-999'].drop(columns=['OccFamName','SOC','SOCName'],
                                errors='ignore').drop_duplicates(subset=['Year','OccFam']), 
                                on=['Year', 'OccFam'], how='left', indicator=True)
    df_aux = pd.concat([
        df_aux[df_aux['_merge'] != 'left_only'],  # Keep the successfully merged ones from first merge
        df_aux2[df_aux2['_merge'] != 'left_only'].drop(columns=['_merge'], errors='ignore')  # Append the successfully merged from second merge
    ], ignore_index=True)
    
    df_aux = pd.concat([
        df_aux,  
        df_aux3.drop(columns=['_merge'], errors='ignore')  # Append the successfully merged from second merge
    ], ignore_index=True)
    df=df_aux
    del df_aux, df_aux2, df_aux3, df_soc, unmatched
    
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
    
    
    # Step 1: Compute Openings
    df['MSAopenings'] = df.groupby(['BestFitMSA'])['BestFitMSA'].transform('count')
    df['FIPSopenings'] = df.groupby(['FIPS'])['FIPS'].transform('count')
    
    # Step 2: Ensure no zeros before log transformation
    for col in ['unemployment_msa', 'unemployment_ct', 'laborForce_msa', 'laborForce_ct']:
        df[col] = df[col].replace(0, np.nan)  # Replace zero with NaN (to compute at the FIPS level if missing)
    
    for col in ['MSAopenings', 'FIPSopenings', 'SOCMSAopenings', 'SOCFIPSpenings', 'NAICSMSAopenings', 'NAICSFIPSpenings']:
        df[col] = df[col].replace(0, np.nan)  # Replace zero with NaN
    
    # Step 3: Compute Measures of Tightness at MSA Level
    df['tight'] = np.log(df['MSAopenings']) - np.log(df['unemployment_msa'])
    df['tight_soc'] = np.log(df['SOCMSAopenings']) - np.log(df['unemployment_msa'])
    df['tight_naics'] = np.log(df['NAICSMSAopenings']) - np.log(df['unemployment_msa'])
    df['vacan'] = np.log(df['MSAopenings']) - np.log(df['laborForce_msa'])
    df['vacan_soc'] = np.log(df['SOCMSAopenings']) - np.log(df['laborForce_msa'])
    df['vacan_naics'] = np.log(df['NAICSMSAopenings']) - np.log(df['laborForce_msa'])
    
    # Step 4: Identify rows where `tight` is NaN (meaning unemployment_msa or MSAopenings was missing)
    missing_tigh_mask = df['tight'].isna()
    
    # Step 5: Compute `tight` and `vacan` for missing cases using FIPS-level data
    df.loc[missing_tigh_mask, 'tight'] = np.log(df.loc[missing_tigh_mask, 'FIPSopenings']) - np.log(df.loc[missing_tigh_mask, 'unemployment_ct'])
    df.loc[missing_tigh_mask, 'tight_soc'] = np.log(df.loc[missing_tigh_mask, 'SOCFIPSpenings']) - np.log(df.loc[missing_tigh_mask, 'unemployment_ct'])
    df.loc[missing_tigh_mask, 'tight_naics'] = np.log(df.loc[missing_tigh_mask, 'NAICSFIPSpenings']) - np.log(df.loc[missing_tigh_mask, 'unemployment_ct'])
    
    df.loc[missing_tigh_mask, 'vacan'] = np.log(df.loc[missing_tigh_mask, 'FIPSopenings']) - np.log(df.loc[missing_tigh_mask, 'laborForce_ct'])
    df.loc[missing_tigh_mask, 'vacan_soc'] = np.log(df.loc[missing_tigh_mask, 'SOCFIPSopenings']) - np.log(df.loc[missing_tigh_mask, 'laborForce_ct'])
    df.loc[missing_tigh_mask, 'vacan_naics'] = np.log(df.loc[missing_tigh_mask, 'NAICSFIPSopenings']) - np.log(df.loc[missing_tigh_mask, 'laborForce_ct'])
    
    # Step 6: Drop temporary columns
    df.drop(columns=['FIPSopenings', 'SOCFIPSpenings', 'NAICSFIPSpenings', 'MSAopenings', 'SOCMSAopenings', 'NAICSMSAopenings'], inplace=True, errors='ignore')
    
    # Garbage collection
    gc.collect()
    
    #3.7 Demographic Composition
    def clean_soc_mapping(df):
        # Drop duplicates to ensure unique pairs
        df = df.drop_duplicates()
        # Strip whitespace from 'SOC' and 'SOCName'
        df['SOC'] = df['SOC'].str.strip()
        df['SOCName'] = df['SOCName'].str.strip()
        
        # Replace commas in the DataFrame
        df['SOCNameb'] = df['SOCName'].replace(',', '', regex=True)
    
        # Clean 'SOCName' column
        df['SOCNameb'] = df['SOCNameb'].str.title()
        df['SOCNameb'] = df['SOCNameb'].replace('--', '-', regex=True)
        df['SOCNameb'] = df['SOCNameb'].str.replace(
            r'(?<=[-/])([a-z])', 
            lambda match: match.group(1).upper(),
            regex=True
        )
    
        return df
    
    df_dem=pd.read_csv(directory + 'Demographic_Composition/dem_occst.csv', delimiter=',') 
    # Apply the function to the column
    df = clean_soc_mapping(df)
    df_dem.rename(columns={'SOCName':'SOCNameb'}, inplace=True)
    df_merge=pd.merge(
                    df, df_dem.drop(columns=['SOCNameb']).drop_duplicates(subset=['SOC','FIPSState','Year']), on=['SOC','FIPSState','Year'], how='left', indicator=True
                )
    difference=df_merge[df_merge['_merge']=='left_only']
    columns_to_drop=['Male','Female','white','black','americanIndian','alaskaNative','asian','hawaiianPacificIslander','someOtherRace','ageMean','_merge']
    df_merge2=pd.merge(
                difference.drop(columns=columns_to_drop), df_dem.drop(columns=['SOC']).drop_duplicates(subset=['SOCNameb','FIPSState','Year']), on=['SOCNameb','FIPSState','Year'], how='left', indicator=True
            )
    df=pd.concat([df_merge[df_merge['_merge']=='both'].drop(columns=['_merge']), df_merge2.drop(columns=['_merge'])],ignore_index=True)
    del df_dem, df_merge, df_merge2
    df.drop(columns=['SOCNameb'], inplace=True)
    
    df_race=pd.read_csv(directory + 'Demographic_Composition/dem_msa.csv', delimiter=',') 
    df=pd.merge(df, df_race, on=['Year','BestFitMSA'],how='left')
    del df_race
    
    #3.8 Labor Productivity
    df_prod=pd.read_parquet(directory + 'Industry_Productivity/industry_all.parquet',engine='pyarrow') 
    df=pd.merge(df, df_prod, on=['Year','Sector','NAICS3','NAICS4','NAICS5','NAICS6'], how='left')
    del df_prod

    #Migration
    df_mig = pd.read_parquet(directory + 'Migration/migration_msa.parquet')
    df_mig=df_mig[df_mig['Year']==df['Year'].max()]
    df_aux=pd.merge(df, df_mig.drop(columns=['Year']), on=['BestFitMSA'], how='left', indicator=True)
    df_mig = pd.read_parquet(directory + 'Migration/migration_ct.parquet',engine='pyarrow')
    difference=df_aux[df_aux['_merge']=='left_only'].drop(columns=['intmig','dommig','_merge'])
    df_aux2=pd.merge(difference, df_mig, on=['Year','FIPSState','FIPSCounty'], how='left')
    df=pd.concat([df_aux[df_aux['_merge']=='both'].drop(columns=['_merge']), df_aux2],ignore_index=True)
    df.drop(columns=['_merge'], inplace=True, errors='ignore')
    del df_mig, df_aux, df_aux2, difference
    
    #Educational Attainment
    df_educ = pd.read_parquet(directory + 'Education/education_ct.parquet',engine='pyarrow')
    df_aux=pd.merge(df, df_educ, on=['Year','FIPSState', 'FIPSCounty'], how='left', indicator=True)
    difference=df_aux[df_aux['_merge']=='left_only'].drop(columns=['college_st','_merge'])
    df_aux2=pd.merge(difference, df_educ.groupby(by=['FIPSState','Year']).mean().drop(columns=['FIPSCounty']), on=['Year','FIPSState'], how='left')
    df=pd.concat([df_aux[df_aux['_merge']=='both'].drop(columns=['_merge']), df_aux2],ignore_index=True)
    df.drop(columns=['_merge'], inplace=True, errors='ignore')
    del df_aux, df_aux2, df_educ
    gc.collect() 
    
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
    
    for var in ['df_aux', 'columns_to_drop', 'df_merge', 'df_prod', 'df_prod_subset', 'difference', 'drop_columns', 'drop_levels', 'higher_levels','level', 'merge_config', 'merge_hierarchy','merge_levels', 'subset']:
    	globals().pop(var, None)
    
    #COMPUSTAT
    df_comp = pd.read_parquet(directory + 'COMPUSTAT/compustat_quarter.parquet',engine='pyarrow')
    
    df=pd.merge(
        df,
        df_comp.drop_duplicates(subset=['clean_company_name','Year','Month']).drop(columns=['conm', 'conml']),
        on=['clean_company_name','Year','Month'],
        how='left'
    )
    
    del df_comp
    gc.collect()

    
    #Skills
    # Generate the corresponding file name
    skills_file_name = file_name.replace("Main", "Skills").replace(".zip", ".parquet")
    # Construct the full file path
    skills_file_path = os.path.join(output_directory, skills_file_name)
    # Load the Parquet file
    df_skills = pd.read_parquet(skills_file_path, engine='pyarrow')
    df_skills["BGTJobId"] = (
    pd.to_numeric(df_skills["BGTJobId"], errors="coerce")  # Convert valid numbers, coerce invalid to NaN
    .fillna(-999)                                   # Replace NaN with a sentinel
    .astype(int)                                     # Convert everything to int
	)
    df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_skills, on=['BGTJobId'], how='inner')
    del df_skills
    gc.collect()

    #Text
    # Generate the corresponding file name
    txt_file_name = file_name.replace("Main", "Text").replace(".zip", ".parquet")
    # Construct the full file path
    txt_file_path = os.path.join(output_directory, txt_file_name)
    # Load the Parquet file
    df_txt = pd.read_parquet(txt_file_path, engine='pyarrow')
    df_txt["BGTJobId"] = (
    pd.to_numeric(df_txt["BGTJobId"], errors="coerce")  # Convert valid numbers, coerce invalid to NaN
    .fillna(-999)                                   # Replace NaN with a sentinel
    .astype(int)                                     # Convert everything to int
)
    df_txt = df_txt.drop(columns=[col for col in df_txt.columns if col.endswith('_terms')])
    df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_txt.drop(columns=['main'], errors='ignore'), on=['BGTJobId'], how='inner')
    df['main_nd'] = (df['main_nd'] > 1).astype(int)
    df['sr_nd'] = (df[['meaningful_work_count', 'environmental_initiatives_count', 'social_initiatives_count']].sum(axis=1) > 1).astype(int)

    del df_txt
    gc.collect()
    
    # Construct the output file name
    output_file_name = file_name.replace('.zip', '.parquet')
    output_file_path = os.path.join(output_directory, output_file_name)
    
    # Save to Parquet
    df.to_parquet(output_file_path, compression='zstd', engine='pyarrow', index=False)
    print(f"Processed and saved: {output_file_path}")
    del df
    gc.collect()


def process_files_for_year(year, main_directory, output_directory):
    """
    Processes all files for a given year using multiprocessing.
    Limits both processes and threads to reduce server load.
    """
    num_workers = 4 # Limit worker processes

    # Set threading limits to prevent excessive CPU use
    os.environ["OMP_NUM_THREADS"] = "3"
    os.environ["MKL_NUM_THREADS"] = "3"
    os.environ["NUMEXPR_NUM_THREADS"] = "3"

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # List all ZIP files in the input directory
    input_path = os.path.join(main_directory, str(year))
    files = [f for f in os.listdir(input_path) if f.endswith('.zip')]

    if not files:
        print(f"⚠️ No files found for {year}. Skipping...")
        return

    file_paths = [os.path.join(input_path, f) for f in files]

    print(f"🔄 Processing {len(file_paths)} files for Year {year} using {num_workers} workers...")

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(process_files, file, output_directory): file for file in file_paths}

        for future in futures:
            try:
                future.result()  # Catch errors
            except Exception as e:
                print(f"❌ Error processing {futures[future]}: {e}")

            # Force garbage collection after each file is processed
            gc.collect()

    print(f"✅ Finished processing all files for Year {year}.")