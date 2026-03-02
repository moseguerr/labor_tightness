#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 21:06:43 2022

@author: mgor
"""
import pandas as pd
import re
import nltk
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from pathlib import Path

df_unem=pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/final_variables/other variables/unemp.csv', delimiter=',', header=0)
df_unem=df_unem.dropna(how='all')
df_unem=df_unem.rename(columns={"Year": "year", "Month":"month", "Area FIPS Code":"BestFitMSA"}, errors="raise")

df_unem.loc[df_unem['month'] < 4, 'quarter'] = 1
df_unem.loc[(df_unem['month'] > 3) & (df_unem['month'] < 7), 'quarter'] = 2
df_unem.loc[(df_unem['month'] > 6) & (df_unem['month'] < 10), 'quarter'] = 3
df_unem.loc[(df_unem['month'] > 9) & (df_unem['month'] < 13), 'quarter'] = 4

df_unem=df_unem[(df_unem['Unemployment Rate'] !='(n)') ]
df_unem['Unemployment Rate'] = df_unem['Unemployment Rate'].astype(float, errors = 'raise')
df_unem['BestFitMSA'] = df_unem['BestFitMSA'].astype(object, errors = 'raise')

df_unem=df_unem.groupby(['year','quarter','BestFitMSA']).mean().reset_index()

aux=pd.read_table('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_mid.csv.zip', delimiter=',', header=0)

aux.BestFitMSA=aux.BestFitMSA.replace({'na': -999})
aux['BestFitMSA'] = aux['BestFitMSA'].astype(int, errors = 'raise')
aux=aux.merge(df_unem, how='left', on=['year', 'quarter', 'BestFitMSA'], indicator=True)

aux.to_csv('global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main.csv.zip', compression='zip', index=False)

