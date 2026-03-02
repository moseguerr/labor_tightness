#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 30 17:51:37 2022

@author: mgor
"""
import pandas as pd
import numpy as np
import csv
import gc
from pathlib import Path

path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2020')
df=pd.DataFrame()
df_firm=pd.DataFrame()

for file in path_txt.glob('*.zip'):
        
        if file.name[0:4]=='main':
            df_aux= pd.read_table(file, delimiter=',', header=0)
            df_aux=df_aux.drop(columns=[ 'JobDate_x', 'IsDuplicate', 'IsDuplicateOf', 'WordFreq','MostCom'])
            df=df.append(df_aux)
            del df_aux
            gc.collect()
            
df_msa=df.groupby(['year','MSA']).agg(
max_csr = pd.NamedAgg(column='main_dict', aggfunc=max),
min_csr = pd.NamedAgg(column='main_dict', aggfunc=min ),
p25_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 25)),
p75_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 75)),
p905_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 90)),
p10_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 10)),
count_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: x.count())).reset_index()

df_msa.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2020/difference_msa.csv.zip', compression='zip', index=False)

del df_msa
gc.collect()

df_firm=df.groupby(['year','Employer']).agg(
max_csr = pd.NamedAgg(column='main_dict', aggfunc=max),
min_csr = pd.NamedAgg(column='main_dict', aggfunc=min ),
p25_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 25)),
p75_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 75)),
p90_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 90)),
p10_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: np.percentile (x, 10)),
count_csr = pd.NamedAgg(column='main_dict', aggfunc=lambda x: x.count())).reset_index()

df_firm.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/2020/difference_firm.csv.zip', compression='zip', index=False)

del df_firm
gc.collect()
