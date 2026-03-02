#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 17:20:46 2022

@author: mgor
"""


import pandas as pd
import numpy as np
import csv
import gc
from pathlib import Path

df=pd.DataFrame()
df2=pd.DataFrame()
for year in range(2010,2022,1):
    path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(year))

    for file in path_txt.glob('*.zip'):

            if file.name[0:3]=='spe':
                df_aux= pd.read_table(file, delimiter=',', header=0)
                df_aux=df_aux.drop(columns=[ 'Unnamed: 0'])
                df2=df2.append(df_aux)
                del df_aux
                gc.collect()
    df2=df2.groupby(['year', 'Employer']).mean()
    df=df.append(df2)
                    

df.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/spec.csv.zip', compression='zip', index=False)


