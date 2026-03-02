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
import numpy as np
import zipfile
from concurrent.futures import ProcessPoolExecutor


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
       
        directory='/global/home/pc_moseguera/data/other_data/'
        #directory='/Users/mgor/Dropbox/Second YPP/Data/Other data/'
        df= pd.read_table(input_file_path , encoding='latin', engine="python", delimiter="\t")
        #1. First Clean
        #########################
        # List of columns to drop
        #1. First Clean
        #########################
        # List of columns to drop
        columns_to_drop = [
            "Edu", "MaxEdu", "MaxDegree", "MinHrlySalary", "MaxHrlySalary", 
            "MaxExp", "Lat", "Lon", "CleanTitle", "BGTOcc", "TaxTerm", 
            "PayFrequency","JobDate","MSA","JobId",'CanonTitle',
            'BGTCareerAreaName2','MSAName','Internship', 'ONET',
            'ONETName','BGTOccName','BGTOccGroupName','Specialty',
            'BGTOccGroupName2','BGTCareerAreaName','BGTCareerAreaName2',
            'BestFitMSAType', 'City', 'NAICS4', 'NAICS5', 'NAICS6']
        
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
        df = df.loc[df['NAICS3'] != -999]
        
        # Drop columns from the DataFrame
        df = df.drop(columns=columns_to_drop, errors="ignore")
        
        # Rename the column 'employer' to 'CanonEmployer'
        df = df.rename(columns={"Employer": "CanonEmployer"}, errors='ignore')
        df = df[df['CanonEmployer'].notna() &  ~df['CanonEmployer'].isin([None, "None", "na"])]
        
        # Convert and filter
        cols_to_convert = [
            "BGTJobId", "BestFitMSA", "FIPSCounty", "FIPS", "FIPSState", "OccFam", "Sector"]
        for col in cols_to_convert:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-999).astype(int)
        
        # List of columns to convert to strings and replace missing values
        string_cols = [
            'BestFitMSAName', 'State', 'County', 'SectorName', 'SOCName', 'OccFamName', 
            'SOC', 'CanonEmployer']
        
        # Convert to string, replace NaN and 'na' with '-999'
        df[string_cols] = df[string_cols].astype(str).replace({'nan': '-999', 'na': '-999', np.nan: '-999'}).apply(lambda x: x.str.strip())
        
        cols_to_filter = ["BGTJobId", "FIPSState", "Sector", "OccFam"]
        df = df.loc[(df[cols_to_filter] != -999).all(axis=1)]
        df = df[~((df['FIPS'] == -999) & (df['BestFitMSA'] == -999))]
        del columns_to_drop, cols_to_convert, cols_to_filter, string_cols
        
        #Variable Transformation
        
        df['Degree'] = df['Degree'].isin(["Bachelor's", "PhD", "Master's"]).astype(int)
        df['boncom'] = df['SalaryType'].isin(['bonus', 'commission']).astype(int)
        df['parttime'] = df['JobHours'].isin(['partime']).astype(int)
        df.drop(columns=['SalaryType','JobHours'], inplace=True, errors='ignore')
        
        
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
        # Identify object columns
        object_cols = df_jolts.select_dtypes(include=['object']).columns
        # Convert each column dynamically
        for col in object_cols:
            df_jolts[col] = pd.to_numeric(df_jolts[col], errors='coerce')  # Convert to numeric (int or float)
            # Convert to int if no decimal values, otherwise keep as float
            if df_jolts[col].dropna().apply(float.is_integer).all():
                df_jolts[col] = df_jolts[col].astype(int)
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
        max_year = df['Year'].max()
        year = str(2021 if max_year == 2022 else max_year)

        # Load the corresponding parquet file
        df_oesm = pd.read_parquet(directory + 'OESM/' + year + '.parquet')
        #df_oesm = pd.read_parquet(directory + 'OESM/All/CLEAN/With Bartik/' + year + '.parquet')
        df_oesm.rename(columns = {'loc_q': 'loc_quotient', 'pct_tot': 'pct_total', 'jobs_1000_orig':'jobs_1000'}, inplace=True, errors='ignore')
        df_oesm.drop(columns=['loc_quotient','pct_total', 'pct_rpt','prim_state', 'i_group','o_group','GROUP','group'], inplace=True, errors='ignore')
        col_drop=['_merge','tot_emp', 'emp_prse',
               'jobs_1000', 'a_mean', 'a_pct10', 'a_pct25', 'a_median', 'a_pct75',
               'a_pct90', 'natEmp', 'a_mean_nt', 'excludedOcc', 'excludedTotal',
               'SOCShare', '0507SOCShare', 'shiftSOC']
        #First Merge
        df_merged = df.merge(df_oesm.drop_duplicates(subset=['BestFitMSA','FIPSState', 'SOC','OccFam']).drop(columns=['SOCName'], errors='ignore'), on=['BestFitMSA', 'FIPSState','SOC','OccFam'], how='left', indicator=True)
        # Separate matched & unmatched rows
        matched = df_merged[df_merged['_merge'] == 'both'].drop(columns=['_merge'])
        unmatched_rows = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=col_drop, errors='ignore')
        #Second Merge
        df_merged = unmatched_rows.merge(
            df_oesm[df_oesm['SOC'] == '-999']
            .drop_duplicates(subset=['BestFitMSA', 'OccFam'])
            .drop(columns=['SOC', 'FIPSState', 'SOCName'], errors='ignore'),
            on=['BestFitMSA', 'OccFam'], 
            how='left', 
            indicator=True
        )
        matched2 = df_merged[df_merged['_merge'] == 'both'].drop(columns=['_merge'])
        unmatched_rows = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=col_drop, errors='ignore')
        #Second Merge
        df_merged = unmatched_rows.merge(
            df_oesm[(df_oesm['SOC'] == '-999') & (df_oesm['BestFitMSA'] == -999)]
            .drop_duplicates(subset=['FIPSState', 'OccFam'])
            .drop(columns=['SOC', 'BestFitMSA', 'SOCName'], errors='ignore'),
            on=['FIPSState', 'OccFam'], 
            how='left', 
            indicator=True
        )
        
        # Separate matched & unmatched rows
        df = pd.concat([matched, matched2, df_merged.drop(columns=['_merge'])], ignore_index=True)
        del df_oesm, df_merged, unmatched_rows, col_drop, matched, matched2, max_year, object_cols
                
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
            how='left', indicator=True
        )
        # Step 5: Concatenate successfully merged data
        df = pd.concat([
        df[df['_merge'] != 'left_only'],  # Keep the successfully merged ones from first merge
        df_aux.drop(columns=['_merge'], errors='ignore')  # Append the successfully merged from second merge
        ], ignore_index=True)
        del df_aux, df_ind, unmatched
        df.drop(columns=['BestFitMSA4'], inplace=True, errors='ignore')
        gc.collect
                
        #3.3 Economic Profile 
        #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/Economic Profile/'
        df_cainc = pd.read_csv(directory + 'Economic Profile/ALL_CAINC.csv', delimiter=',', encoding='latin')
        df_cainc = df_cainc[df_cainc['Year'] == df['Year'].unique()[0]]
        df=pd.merge(df,df_cainc, on=['FIPS', 'FIPSState', 'FIPSCounty', 'Year'],how='left')
        del df_cainc
        gc.collect()
         
        #3.4 GDP
        #extract_dir = '/Users/mgor/Library/CloudStorage/Dropbox/Second YPP/Data/Other data/GDP/'
        df_cagdp = pd.read_csv(directory + 'GDP/ALL_CAGDP.csv', delimiter=',', encoding='latin')
        df_cagdp = df_cagdp[df_cagdp['Year'] == df['Year'].unique()[0]]
        df.drop(columns=['_merge'], inplace=True, errors='ignore')
        df=pd.merge(df, df_cagdp.drop(columns=['Year']), on=['FIPSState', 'FIPSCounty','Sector'], how='left', indicator=True)
        unmatched = df[df['_merge'] == 'left_only'].drop(columns=['_merge','lgdp_change'], errors='ignore')
        df_merge = pd.merge(
            unmatched, df_cagdp[df_cagdp['FIPSCounty'] == -999]  # ✅ Corrected filtering condition
                .drop_duplicates(subset=['FIPSState', 'Sector'])
                .drop(columns=['Year', 'FIPSCounty']), 
            on=['FIPSState', 'Sector'], 
            how='left')
        df=pd.concat([df[df['_merge']=='both'], df_merge], ignore_index=True)
        del df_cagdp, df_merge, unmatched
        
        #By industry-quarter + crisis
        df_ind = pd.read_parquet(directory + 'Industry Productivity/gdpchange_quarter.parquet')
        df.drop(columns=['_merge'], inplace=True, errors='ignore')
        df_merge=pd.merge(df, df_ind.drop_duplicates(subset=['NAICS3','Sector','Year','Month']), on=['NAICS3','Sector','Year','Month'], how='left', indicator=True)
        unmatched = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge','igdpq_ch'], errors='ignore')
        matched = df_merge[df_merge['_merge'] == 'both'].drop(columns=['_merge'], errors='ignore')
        df_merge = pd.merge(unmatched, df_ind[df_ind['NAICS3'] == -999]  # ✅ Corrected filtering condition
                .drop_duplicates(subset=['Sector','Year','Month'])
                .drop(columns=['NAICS3']),on=['Sector','Year','Month'], how='left')
        df = pd.concat([matched, df_merge], ignore_index=True)
        del df_ind, unmatched, matched, df_merge
        
        df_crisis = pd.read_parquet(directory + 'Industry Productivity/gdp_crisis.parquet')
        df=pd.merge(df, df_crisis.drop_duplicates(subset=['NAICS3','Sector','Month']), on=['NAICS3','Sector','Month'], how='left', indicator=True)
        unmatched = df[df['_merge'] == 'left_only'].drop(columns=['_merge','crisis_ch'], errors='ignore')
        matched = df[df['_merge'] == 'both'].drop(columns=['_merge'], errors='ignore')
        df_merge = pd.merge(unmatched, df_crisis[df_crisis['NAICS3'] == -999]  # ✅ Corrected filtering condition
                .drop_duplicates(subset=['Sector','Month'])
                .drop(columns=['NAICS3']), on=['Sector','Month'], how='left')
        df = pd.concat([matched, df_merge], ignore_index=True)
        del df_crisis, matched, unmatched, df_merge
        
        #3.5 Unionization
        df_loc = pd.read_csv(directory + 'Union/loc_union.csv')
        df_ind=pd.read_csv(directory + 'Union/industry.csv')
        df_soc=pd.read_csv(directory + 'Union/soc_union.csv')
        #Location Based
        df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_loc[df_loc['BestFitMSA']!=-999].drop(columns=['FIPSState'], errors='ignore'), on=['Year', 'BestFitMSA'], how='left', indicator=True)
        unmatched = df[df['_merge'] == 'left_only'].drop(columns=['_merge','lpctunion'], errors='ignore')
        # Step 4: Second merge using FIPSState 
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
        del df_loc, df_aux, unmatched
        
        #Industry
        df.drop(columns=['_merge'],inplace=True, errors='ignore')
        df_ind=df_ind[(df_ind['NAICS4'] == -999)].drop_duplicates(subset=['Year', 'Sector', 'NAICS3']).drop(columns=['NAICS4', 'NAICS5','NAICS6'])
        df_aux=pd.merge(df,df_ind , on=['Year', 'Sector', 'NAICS3'],how='left', indicator=True)
        matched = df_aux[df_aux['_merge'] == 'both'].drop(columns=['_merge'], errors='ignore')
        unmatched = df_aux[df_aux['_merge'] == 'left_only'].drop(columns=['_merge','pctunion_ind'], errors='ignore')
        df_aux2=pd.merge(unmatched,df_ind[(df_ind['NAICS3'] == -999) & (df_ind['Sector'] != -999)]  
                .drop_duplicates(subset=['Year','Sector'])
                .drop(columns=['NAICS3']), 
            on=['Year','Sector'], 
            how='left')
        df = pd.concat([
            matched,  # Keep the successfully merged ones from first merge
            df_aux2], ignore_index=True)
        del df_ind, matched, unmatched, df_aux2

        
        #Occupation
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
            df_aux2[df_aux2['_merge'] != 'left_only'].drop(columns=['_merge'], errors='ignore'),  # Append the successfully merged from second merge
            df_aux3.drop(columns=['_merge'], errors='ignore') 
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
            df, df_county.drop(columns=['FIPS']), on=['FIPSState','FIPSCounty','Year', 'Month'], how='left'
        )
        del df_county
        
        
        # Define main grouping categories
        msa_group = ['BestFitMSA']
        fips_group = ['FIPS']
        employer_group = ['CanonEmployer']  # Unified employer group
        occ_group = ['OccFam']
        sector_group = ['Sector']
        
        # Define general grouping categories
        general_groupings = {
            'MSAopenings': msa_group,
            'FIPSopenings': fips_group,
            'MSAOccopenings': msa_group + occ_group,
            'FIPSOccopenings': fips_group + occ_group,
            'MSASectoropenings': msa_group + sector_group,
            'FIPSSectoropenings': fips_group + sector_group
        }
        
        # Define employer-based extensions dynamically
        employer_extensions = {
            f"{gen_col}_employer": employer_group + group_cols
            for gen_col, group_cols in general_groupings.items()
        }
        
        # Combine both into one dictionary for iteration
        grouping_patterns = {**general_groupings, **employer_extensions}
        
        # Apply grouping and log transformation
        for new_col, group_cols in grouping_patterns.items():
            # Compute count of openings at the respective level
            df[new_col] = df.groupby(group_cols)[group_cols[0]].transform('count')
            
            # Log transformation
            df[new_col] = np.log(df[new_col])  # Log transformation assumes counts ≥1
        
        # Compute TopQuartile indicator correctly
        for new_col in employer_extensions.keys():  # Only employer-based columns
            general_col = new_col.replace('_employer', '')  # Extract general column name
            
            # Compute the 75th percentile **per general group**
            quantiles = df.groupby(general_groupings[general_col])[general_col].quantile(0.75)
            
            # Map the quantiles back to df and compute the leave one out
            df[f'TopQuartile{general_col}'] = (df[new_col] >= df[general_col].map(quantiles)).fillna(-0).astype(int)
            df[general_col]=df[general_col]-df[new_col]
        
        
        cols_to_convert = ['unemployment_msa', 'unemployment_ct','employment_msa', 'employment_ct', 'laborForce_msa', 'laborForce_ct']
        for col in cols_to_convert:
            # Convert to float
            df[col] = df[col].replace({'(n)': np.nan, 'N/A': np.nan, '-': np.nan, 'na': np.nan})
            df[col] = df[col].astype(float)
            # Replace zeros with epsilon but keep NaNs unchanged
            df[col] = df[col].apply(lambda x: np.finfo(float).eps if x == 0 else x)
            # Apply log transformation
            df[col] = np.log(df[col])
        
        # Step 2: Compute Measures of Tightness and Vacancy at MSA Level
        df['tight'] = df['MSAopenings'] - df['unemployment_msa']
        df['vacan'] = df['MSAopenings'] - df['laborForce_msa']
        df['tightocc'] = df['MSAOccopenings'] - df['unemployment_msa']
        df['vacanocc'] = df['MSAOccopenings'] - df['laborForce_msa']
        df['tightsector'] = df['MSASectoropenings'] - df['unemployment_msa']
        df['vacansector'] = df['MSASectoropenings'] - df['laborForce_msa']
        
        # Step 3: Identify rows where `tight` is NaN (i.e., missing unemployment or vacancies)
        missing_tight_mask = df['tight'].isna()
        
        # Step 4: Fill Missing `tight` and `vacan` using FIPS-Level Data
        df.loc[missing_tight_mask, 'tight'] = df.loc[missing_tight_mask, 'FIPSopenings'] - df.loc[missing_tight_mask, 'unemployment_ct']
        df.loc[missing_tight_mask, 'vacan'] = df.loc[missing_tight_mask, 'FIPSopenings'] - df.loc[missing_tight_mask, 'laborForce_ct']
        df.loc[missing_tight_mask, 'tightocc'] = df.loc[missing_tight_mask, 'FIPSOccopenings'] - df.loc[missing_tight_mask, 'unemployment_ct']
        df.loc[missing_tight_mask, 'vacanocc'] = df.loc[missing_tight_mask, 'FIPSOccopenings'] - df.loc[missing_tight_mask, 'laborForce_ct']
        df.loc[missing_tight_mask, 'tightsector'] = df.loc[missing_tight_mask, 'FIPSSectoropenings'] - df.loc[missing_tight_mask, 'unemployment_ct']
        df.loc[missing_tight_mask, 'vacansector'] = df.loc[missing_tight_mask, 'FIPSSectoropenings'] - df.loc[missing_tight_mask, 'laborForce_ct']
   
        
        # Drop columns
        df = df.drop(columns=list(general_groupings.keys()), errors='ignore')
        df['unemploymentRate_msa'] = pd.to_numeric(df['unemploymentRate_msa'], errors='coerce')
        df['unemploymentRate_ct'] = pd.to_numeric(df['unemploymentRate_ct'], errors='coerce')
        
        del general_groupings, employer_extensions, msa_group, fips_group, sector_group, occ_group,missing_tight_mask, group_cols, grouping_patterns, new_col, general_col, quantiles
        
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
        #df_dem=pd.read_csv(directory + 'Age/dem_occst.csv', delimiter=',') 
        
        # Apply the function to the column
        df = clean_soc_mapping(df)
        df_dem.rename(columns={'SOCName':'SOCNameb'}, inplace=True)
        df.drop(columns=['_merge'], inplace=True,  errors='ignore')
        df_merge=pd.merge(
                        df, df_dem.drop(columns=['SOCNameb']).drop_duplicates(subset=['SOC','FIPSState','Year']), on=['SOC','FIPSState','Year'], how='left', indicator=True
                    )
        difference=df_merge[df_merge['_merge']=='left_only']
        columns_to_drop=['Male','Female','white','black','americanIndian','alaskaNative','asian','hawaiianPacificIslander','someOtherRace','ageMean','_merge']
        df_merge2=pd.merge(
                    difference.drop(columns=columns_to_drop), df_dem.drop(columns=['SOC']).drop_duplicates(subset=['SOCNameb','FIPSState','Year']), on=['SOCNameb','FIPSState','Year'], how='left', indicator=True
                )
        df=pd.concat([df_merge[df_merge['_merge']=='both'].drop(columns=['_merge']), df_merge2.drop(columns=['_merge'])],ignore_index=True)
        del df_dem, df_merge, df_merge2, difference
        df.drop(columns=['SOCNameb'], inplace=True)
        
        df_race=pd.read_csv(directory + 'Demographic_Composition/dem_msa.csv', delimiter=',') 
        #df_race=pd.read_csv(directory + 'Race/dem_msa.csv', delimiter=',') 
        
        df=pd.merge(df, df_race, on=['Year','BestFitMSA'],how='left')
        del df_race
        
        #3.8 Labor Productivity
        df_prod=pd.read_parquet(directory + 'Industry Productivity/industry_all.parquet',engine='pyarrow') 
        df_prod=df_prod[df_prod['NAICS4']==-999].drop(columns=['NAICS4', 'NAICS5','NAICS6']).drop_duplicates(subset=['Year', 'Sector', 'NAICS3'])
        df=pd.merge(df, df_prod, on=['Year','Sector','NAICS3'], how='left')
        del df_prod
        
        #Migration
        df_mig = pd.read_parquet(directory + 'Migration/migration_msa.parquet')
        #df_mig = pd.read_parquet(directory + 'Population/migration_msa.parquet')
        df_mig=df_mig[df_mig['Year']==df['Year'].max()]
        df_aux=pd.merge(df, df_mig.drop(columns=['Year']), on=['BestFitMSA'], how='left', indicator=True)
        
        df_mig = pd.read_parquet(directory + 'Migration/migration_ct.parquet',engine='pyarrow')
        #df_mig = pd.read_parquet(directory + 'Population/migration_ct.parquet',engine='pyarrow')
        difference=df_aux[df_aux['_merge']=='left_only'].drop(columns=['intmig','dommig','_merge'])
        df_aux2=pd.merge(difference, df_mig, on=['Year','FIPSState','FIPSCounty'], how='left')
        df=pd.concat([df_aux[df_aux['_merge']=='both'].drop(columns=['_merge']), df_aux2],ignore_index=True)
        df.drop(columns=['_merge'], inplace=True, errors='ignore')
        del df_mig, df_aux, df_aux2, difference
        
        #Educational Attainment
        df_educ = pd.read_parquet(directory + 'Educational Attainment/education_ct.parquet',engine='pyarrow')
        df_aux=pd.merge(df, df_educ, on=['Year','FIPSState', 'FIPSCounty'], how='left', indicator=True)
        difference=df_aux[df_aux['_merge']=='left_only'].drop(columns=['college_st','_merge'])
        df_aux2=pd.merge(difference, df_educ.groupby(by=['FIPSState','Year']).mean().drop(columns=['FIPSCounty']), on=['Year','FIPSState'], how='left')
        df=pd.concat([df_aux[df_aux['_merge']=='both'].drop(columns=['_merge']), df_aux2],ignore_index=True)
        df.drop(columns=['_merge'], inplace=True, errors='ignore')
        del df_aux, df_aux2, df_educ, difference
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
        df['nonprofit'] = pd.to_numeric(df['nonprofit'], errors='coerce')
        
        #COMPUSTAT
        df_comp = pd.read_parquet(directory + 'COMPUSTAT/compustat_quarter.parquet',engine='pyarrow')
        df_comp.replace([np.inf, -np.inf], np.nan, inplace=True)

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
        skills_file_path = os.path.join(output_path, skills_file_name)
        # Load the Parquet file
        df_skills = pd.read_parquet(skills_file_path, engine='pyarrow')
        df_skills["BGTJobId"] = (pd.to_numeric(df_skills["BGTJobId"], errors="coerce").fillna(-999).astype(int))
        df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_skills, on=['BGTJobId'], how='inner')
        del df_skills, skills_file_name, skills_file_path
        gc.collect()
        
        #Text
        # Generate the corresponding file name
        txt_file_name = file_name.replace("Main", "Text").replace(".zip", ".parquet")
        # Construct the full file path
        txt_file_path = os.path.join(output_path, txt_file_name)
        # Load the Parquet file
        df_txt = pd.read_parquet(txt_file_path, engine='pyarrow')
        df_txt["BGTJobId"] = (pd.to_numeric(df_txt["BGTJobId"], errors="coerce").fillna(-999).astype(int))
        df_txt = df_txt.drop(columns=[col for col in df_txt.columns if col.endswith('_terms')])
        df=pd.merge(df.drop(columns=['_merge'], errors='ignore'), df_txt.drop(columns=['main'], errors='ignore'), on=['BGTJobId'], how='inner')
        # Step 1: Identify all columns ending with "_count"
        count_cols = [col for col in df.columns if col.endswith('_count')]
        # Step 2: Compute total count per row
        df['total_count'] = df[count_cols].sum(axis=1)
        df['sr_count'] = (df[['meaningful_work_count', 'environmental_initiatives_count', 'social_initiatives_count']].sum(axis=1))
        df.rename(columns={'main_nd':'main_count'}, inplace=True, errors='ignore')
        count_cols = [col for col in df.columns if col.endswith('_count')]
        # Step 3: Create _prop columns
        for col in count_cols:
            new_col_name = col.replace('_count', '_prop')  # Remove '_count' and replace with '_prop'
            df[new_col_name] = df[col] / df['total_count']
        # Step 4: Transform _count columns (set to 1 if >1)
        df[count_cols] = (df[count_cols] > 1).astype(int)
        # Step 5: Group by CanonEmployer, BestFitMSA, FIPS, NAICS6, SOC and sum _count values, then merge back
        df[count_cols] = df.groupby(['CanonEmployer', 'FIPSState','BestFitMSA', 'FIPS', 'NAICS3', 'SOC'])[count_cols].transform('sum')
        df.drop(columns=['total_count', 'total_prop'], inplace=True, errors='ignore')
        del df_txt, count_cols, col, txt_file_name, txt_file_path
        gc.collect()
        
        df['Openingstotal_employer'] = df.groupby(['CanonEmployer', 'FIPSState', 'BestFitMSA', 'FIPS', 'NAICS3', 'SOC'])['CanonEmployer'].transform('count')
        
        #Final cleaning
        df.drop(columns=['clean_company_name','month'], inplace=True, errors='ignore')
        
        # Define columns that should be strings
        string_cols = [
            'gvkey', 'tic', 'cusip', 'comCounty', 'comDom', 'comCountry', 'comHeadquarters',
            'OccFamName', 'SOC', 'SOCName', 'CanonEmployer', 'SectorName', 'State', 
            'County', 'BestFitMSAName'
        ]
        
        # Convert specified columns to string and replace NaN/'na' with '999'
        df[string_cols] = df[string_cols].astype(str).replace({'nan': '-999', 'na': '-999', np.nan: '-999'})
        
        # Convert remaining columns to numeric (int if possible, else float), replacing NaN with -999
        numeric_cols = [col for col in df.columns if col not in string_cols]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric
            df[col] = df[col].fillna(-999)  # Replace NaN with -999
        
            # Convert to int if all values are whole numbers
            if np.issubdtype(df[col].dtype, np.floating):  # Check if column is float
                if (df[col] % 1 == 0).all():  # Check if all values are whole numbers
                    df[col] = df[col].astype(int)
        
        del string_cols, numeric_cols
        
        # List of columns to group by
        groupby_cols = ['gvkey', 'tic', 'cusip', 'comCounty', 'comDom', 'comCountry', 'comNAICS', 'comHeadquarters', 
            'OccFam', 'OccFamName', 'SOC', 'SOCName', 'CanonEmployer', 'Sector', 'SectorName', 
            'NAICS3', 'State', 'County', 
            'FIPSState', 'FIPSCounty', 'FIPS', 'BestFitMSA', 'BestFitMSAName', 'Year', 'Month', 'qtr']
        
        numeric_cols = [col for col in df.columns if col not in groupby_cols]
        df[numeric_cols] = df[numeric_cols].replace(-999, np.nan)
        
        df = df.dropna(subset=['tight', 'bartik'])
        
        # Grouping and aggregating
        df = df.groupby(by=groupby_cols).mean().reset_index()

        # ✅ Save to Parquet (no threading needed for writing)
        df.to_parquet(output_file_path, engine="pyarrow", compression='zstd', index=False)
        print(f"✔ Saved: {output_file_path}")

        # ✅ Free memory
        del df
        gc.collect()

    except Exception as e:
        print(f"❌ Error processing {file_name}: {e}")


def process_main_files(year, main_directory, output_directory, max_workers=4):
    """
    Parallelizes processing of all files for a given year.
    """
    # Set threading limits to prevent excessive CPU use
    os.environ["OMP_NUM_THREADS"] = "3"
    os.environ["MKL_NUM_THREADS"] = "3"
    os.environ["NUMEXPR_NUM_THREADS"] = "3"
    
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
    main_directory = '/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Main/'
    output_directory = '/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'

    for year in years:
        process_main_files(year, main_directory, output_directory, max_workers=4)
