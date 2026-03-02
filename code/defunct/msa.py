#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 04:50:25 2022

@author: mgor
"""
import pandas as pd
import re
import nltk
import numpy as np
import gc
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from pathlib import Path

yy=str(2010)
path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+yy)
df=pd.DataFrame()
df2=pd.DataFrame()

##Compustat
df_compustat=pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/final_variables/other variables/compustat_data_clean.csv', delimiter=',', header=0)



for file in path_txt.glob('*.zip'):

        if file.name[0:3]=='spe':
            df_exm= pd.read_table(file, delimiter=',', header=0)
            df=df.append(df_exm)
            del df_exm
            gc.collect()
            
        if file.name[0:3]=='sum':
            df_aux= pd.read_table(file, delimiter=',', header=0)
            df2=df2.append(df_aux)
            del df_aux
            gc.collect()
            
df.loc[df['month'] < 4, 'quarter'] = 1
df.loc[(df['month'] > 3) & (df['month'] < 7), 'quarter'] = 2
df.loc[(df['month'] > 6) & (df['month'] < 10), 'quarter'] = 3
df.loc[(df['month'] > 9) & (df['month'] < 13), 'quarter'] = 4

df2.loc[df2['month'] < 4, 'quarter'] = 1
df2.loc[(df2['month'] > 3) & (df2['month'] < 7), 'quarter'] = 2
df2.loc[(df2['month'] > 6) & (df2['month'] < 10), 'quarter'] = 3
df2.loc[(df2['month'] > 9) & (df2['month'] < 13), 'quarter'] = 4


df=df.groupby(['year','quarter' ,'Employer','gvkey','MSA']).mean().reset_index()
df2=df2.groupby(['year','quarter' ,'Employer','gvkey','MSA']).sum().reset_index()
df.gvkey = df.gvkey.astype(int, errors = 'raise')
df2.gvkey = df2.gvkey.astype(int, errors = 'raise')
df=df.merge(df2, how='left', on=['gvkey','year','quarter','MSA'])
df=df.merge(df_compustat, how='left', on=['gvkey','year','quarter'])
           

          
df.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+yy+'/comp'+yy+'.csv.zip', compression='zip', index=False)




