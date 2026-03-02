#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 18:24:27 2022

@author: mgor
"""


import pandas as pd
import numpy as np
import csv
import gc
from pathlib import Path


df=pd.DataFrame()
df2=pd.DataFrame()
df3=pd.DataFrame()
df4=pd.DataFrame()

def max_min(x):
    return x.max() - x.min()

for year in range(2010,2022,1):
    path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(year))

    for file in path_txt.glob('*.zip'):

            if file.name[0:4]=='main':
                df_aux= pd.read_table(file, delimiter=',', header=0)
                df2=df2.append(df_aux)
                df3=df3.append(df_aux)
                del df_aux
                gc.collect()
    df2=df2.groupby(['year','SOCName']).agg(({'main_dict':['max', 'min', max_min, 'count','mean']})).reset_index()
    df2.columns=['_'.join(col) if type(col) is tuple else col for col in df2.columns.values]

    df3=df3.groupby(['year', 'Employer']).agg(({'main_dict':['max', 'min', max_min, 'count','mean']})).reset_index()
    df3.columns=['_'.join(col) if type(col) is tuple else col for col in df3.columns.values]

    df=df.append(df2)
    df4=df4.append(df3)
                    

df.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/diff_soc.csv.zip', compression='zip', index=False)
df4.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/diff_firm.csv.zip', compression='zip', index=False)

