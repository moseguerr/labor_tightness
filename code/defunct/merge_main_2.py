#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 18:47:54 2022

@author: mgor
"""
import pandas as pd
import numpy as np
import csv
from pathlib import Path
import gc

yy=2010

path_txt=Path('/global/home/pc_moseguera/data/Burning Glass 2/final_variables/'+str(yy)+'/no_text')
path_main=Path('/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Main/'+str(yy))

def max_min(x):
    return x.max() - x.min()

def per_90(x):
    return x.quantile(0.90)

def per_10(x):
    return x.quantile(0.10)

for mm in range(1,13,1):
    df=pd.DataFrame()
    ### Txt by month
    for file in path_txt.glob('*.zip'):
        month_start=int(file.name[27:29])
        
        if len(file.name)<40:
            month_end=0
            
        else:
            month_end=int(file.name[36:38])
        
        if month_start==mm:
            df_aux= pd.read_table(file, delimiter=',', header=0)
            df_aux=df_aux[(df_aux['month']==mm)]
            df_aux=df_aux.rename(columns={"JobID" :"BGTJobId"})
            df=df.append(df_aux)
        
        elif month_end==mm:
            df_aux= pd.read_table(file, delimiter=',', header=0)
            df_aux=df_aux[(df_aux['month']==mm)]
            df_aux=df_aux.rename(columns={"JobID" :"BGTJobId"})
            df=df.append(df_aux)
    
    ### Merge with main
    for ff in path_main.glob('*.zip'):
        month=int(ff.name[10:12])
        
        if month==mm:
            df_main= pd.read_table(ff, encoding='latin')
            df=df.merge(df_main, how='left', on='BGTJobId')
    
    df.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/main'+str(mm)+'.csv.zip', compression='zip', index=False)

   ## Main aggregate
    df_collapsed=df.groupby(['year','month','MSA','Employer','SectorName','OccFam','OccFamName', 'SOC', 'SOCName', 'ONET', 'ONETName','NAICS6','Lat', 'Lon', 'State']).agg(({'main_dict':['max','min',per_90, per_10,'median','count','mean','std',max_min],
                                                'employee':['max','min','median','mean','std', max_min],
                                                'environment':['max','min','median','mean','std',max_min],
                                                'human_rights':['max','min','median','mean','std',max_min],
                                                'soc_com':['max','min','median','mean','std', max_min]})).reset_index()
    df_collapsed.columns=['_'.join(col) if type(col) is tuple else col for col in df_collapsed.columns.values]
    df_collapsed.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/collapsed'+str(mm)+'.csv.zip', compression='zip', index=False)
    del df_collapsed
    
    ## Sector-Time
    df_sec=df.groupby(['year','SectorName']).agg(({'main_dict':['max','min','median','count','mean','std',max_min],
                                                'employee':['max','min','median','mean','std', max_min],
                                                'environment':['max','min','median','mean','std',max_min],
                                                'human_rights':['max','min','median','mean','std',max_min],
                                                'soc_com':['max','min','median','mean','std', max_min]})).reset_index()
    df_sec.columns=['_'.join(col) if type(col) is tuple else col for col in df_sec.columns.values]
    df_sec.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/sec'+str(mm)+'.csv.zip', compression='zip', index=False)
    del df_sec

    ## Occ-Time
    df_occ=df.groupby(['year','OccFamName']).agg(({'main_dict':['max','min','median','count','mean','std',max_min],
                                                'employee':['max','min','median','mean','std', max_min],
                                                'environment':['max','min','median','mean','std',max_min],
                                                'human_rights':['max','min','median','mean','std',max_min],
                                                'soc_com':['max','min','median','mean','std', max_min]})).reset_index()
    df_occ.columns=['_'.join(col) if type(col) is tuple else col for col in df_occ.columns.values]
    
    df_occ.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/occ'+str(mm)+'.csv.zip', compression='zip', index=False)
    
    del df_occ
    
    ### Differences across MSA within the same firm within the same occupation

    df_fim_occ=df.groupby(['year','Employer','OccFamName']).agg(({'main_dict':['max','min','median','count','mean','std',max_min]})).reset_index()
    df_fim_occ.columns=['_'.join(col) if type(col) is tuple else col for col in df_fim_occ.columns.values]
    
    df_fim_occ.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/fim_occ'+str(mm)+'.csv.zip', compression='zip', index=False)
    del df_fim_occ
    
    ## Difference in CSR within firms across occupations and MSAs
    df_fim=df.groupby(['year','Employer']).agg(({'main_dict':['max','min','median','count','mean','std',max_min]})).reset_index()
    df_fim.columns=['_'.join(col) if type(col) is tuple else col for col in df_fim.columns.values]
    df_fim.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/fim'+str(mm)+'.csv.zip', compression='zip', index=False)
    del df_fim

    ### Time
    df_time=df.groupby(['year']).agg(({'main_dict':['max','min',per_90, per_10,'median','count','mean','std',max_min],
                                                'employee':['max','min','median','mean','std', max_min],
                                                'environment':['max','min','median','mean','std',max_min],
                                                'human_rights':['max','min','median','mean','std',max_min],
                                                'soc_com':['max','min','median','mean','std', max_min]})).reset_index()
    df_time.columns=['_'.join(col) if type(col) is tuple else col for col in df_time.columns.values]
    
    df_time.to_csv('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'+str(yy)+'/time'+str(mm)+'.csv.zip', compression='zip', index=False)
    
    del df_time

    del df
   
    gc.collect()
