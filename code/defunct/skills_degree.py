#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 14:22:26 2022

@author: mgor
"""
import pandas as pd
import numpy as np
import csv
import gc


month=['01','02','03','04','05','06','07','08','09','10','11','12']
for mm in month:
    ### Read main
    df= pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2018/main'+mm+'.csv.zip', delimiter=',', header=0)
    df=df.drop(columns=[ 'JobDate_x', 'IsDuplicate', 'IsDuplicateOf', 'WordFreq','MostCom'])
    
    ### Skills by month
    
    df_skills= pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Skill/2018/Skills_2018-'+mm+'.zip', encoding='latin')
    df_skills=df_skills.drop(columns=[ 'JobDate', 'Skill', 'SkillCluster', 'SkillClusterFamily',
        'IsBaseline', 'IsSoftware', 'Salary'])
    df_skills=df_skills.groupby(['BGTJobId']).max().reset_index()
    df=df.merge(df_skills, how='left', on='BGTJobId')
    
    
    ### Degree by month
 
    df_degree= pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Degree/2018/Degree_2018-'+mm+'.zip', encoding='latin')
    df_degree=df_degree.drop(columns=[ 'JobDate', 'Salary'])
    df_degree=df_degree.groupby(['BGTJobId']).min().reset_index()
    df=df.merge(df_degree, how='left', on='BGTJobId')
    
    df.to_csv('/Users/mgor/Documents/Strategy/2YP/Data/data_csv/test/out/mainfull'+mm+'.csv.zip', compression='zip', index=False)

    ### Collapse
    
    df_collapsed=df.groupby(['year','month','Employer']).mean().reset_index()
    df_collapsed.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2018/spe'+mm+'.csv.zip', compression='zip', index=False)


    del df
    del df_collapsed

    gc.collect()