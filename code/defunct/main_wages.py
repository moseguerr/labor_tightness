#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 11:36:10 2022

@author: mgor
"""


import pandas as pd
import numpy as np
import csv
import gc
from pathlib import Path

### Graph Differences 
df_main=pd.DataFrame()
BGT_list=pd.DataFrame()

for year in range(2010,2022,1):
    path_firm=Path('/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Main/'+str(year))

    for file in path_firm.glob('*.zip'):

        df_aux= pd.read_table(file, delimiter=',', header=0)
        df_aux2=pd.DataFrame()
        df_aux2['BGTJobId']=df_aux[df_aux.MinSalary != -999]['BGTJobId']
        df_aux=df_aux[df_aux.MinSalary != -999]
        df_main=df_main.append(df_aux)
        BGT_list=BGT_list.append(df_aux2)
        del df_aux
        del df_aux2
        gc.collect()

df_main.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/Gender/Main/main_wages.csv.zip', compression='zip', index=False)
BGT_list.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/Gender/Main/jobid_wages.csv.zip', compression='zip', index=False)



