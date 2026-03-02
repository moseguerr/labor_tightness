#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 18:36:35 2022

@author: mgor
"""


import pandas as pd
import numpy as np
import csv

df_aux= pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/test/merged_2021.zip', delimiter=',', header=0)
df_aux=df_aux.iloc[1:100]

df_aux.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2021/test_2021.zip', compression='zip', index=False)