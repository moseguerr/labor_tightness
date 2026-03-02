#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 31 18:47:35 2022

@author: mgor
"""
import pandas as pd
import numpy as np
import csv
import gc
from pathlib import Path

df=pd.DataFrame()

for year in range(2010,2022,1):
    path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(year))

    for file in path_txt.glob('*.zip'):

            if file.name[0:4]=='comp':
                df_aux= pd.read_table(file, delimiter=',', header=0)
                df=df.append(df_aux)
                del df_aux
                gc.collect()

df.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel.csv.zip', compression='zip', index=False)


