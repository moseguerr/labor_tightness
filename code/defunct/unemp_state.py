#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 20:14:57 2022

@author: mgor
"""


import pandas as pd


###Read files
df_aux=pd.read_stata('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main.dta')
df_unem=pd.read_stata('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/unem_state_comp.dta') 

df_aux=df_aux[(df_aux._merge == 'both') ] 
df_aux=df_aux.drop(['_merge'],axis=1)

df_unem1=df_unem.rename(columns={ 'unemployment_rate':'unem_ST'})
df_unem1=df_unem1.drop(['index','ST','name_bgt','employer','gvkey'],axis=1)

df_aux=df_aux.merge(df_unem1, how='left', on=['year','quarter','ST_FIPS_Code'], indicator=True)

df_unem=df_unem.rename(columns={ 'unem_ST':'unem_head', 'ST_FIPS_Code':'ST_head'})
df_unem=df_unem.drop(['ST','gvkey','name_bgt','index'],axis=1)
df_aux=df_aux.rename(columns={ '_merge':'merge_1'})

df_aux=df_aux.merge(df_unem, how='left', on=['year','quarter','employer'], indicator=True)

df_aux.to_stata('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main_ST.dta')

