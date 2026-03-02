#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 15:19:47 2022

@author: mgor
"""

### Import packages
import pandas as pd
import numpy as np
import csv
import string 
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords as sw
from nltk.collocations import *
bg = nltk.collocations.BigramAssocMeasures()
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import random
import datetime
import re
import os
from multiprocessing import  Pool
from pathlib import Path
import gc

### Set paths
os.chdir("/global/home/pc_moseguera/code")

### Read Table 
#df_2022=pd.read_table('../data/Burning Glass 2/Processed/merged_2022.zip', delimiter=',', header=0)

### Read dictionaries
df_dict=pd.read_table('../data/Burning Glass 2/Processed/main_decomposed.csv', delimiter=',', header=0)

### Wilmers and Zhang
wil_zha_full=df_dict['wil_zha'].str.strip().str.replace('_', ' ').dropna().tolist()
wil_zha_career=df_dict['wil_zha_career'].str.strip().str.replace('_', ' ').dropna().tolist()
wil_zha_life=df_dict['wil_zha_life'].str.strip().str.replace('_', ' ').dropna().tolist()

### Wilmers+Pencle+Arm
emp_ben=df_dict['employee benefits'].str.strip().str.replace('_', ' ').dropna().tolist()
values_purp=df_dict['values and social purpose'].str.strip().str.replace('_', ' ').dropna().tolist()
career=df_dict['career meaning and work environment '].str.strip().str.replace('_', ' ').dropna().tolist()
worklife=df_dict['work-life'].str.strip().str.replace('_', ' ').dropna().tolist()
environ=df_dict['environmental action'].str.strip().str.replace('_', ' ').dropna().tolist()
gover=df_dict['governance-transparency'].str.strip().str.replace('_', ' ').dropna().tolist()
main=emp_ben+values_purp+career+worklife+environ+gover

### Paralellize function
def parallelize_dataframe(df, func, n_cores=6):
    df_split = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df

### Definition of count function   
def keyword_count(doc, keyword_list):
    return sum([doc.count(keyword) for keyword in keyword_list])

### Define function that creates list of words 

def keyword_list(doc, keyword_list):
    word=[]
    for keyword in keyword_list:
        if keyword in doc:
            word.append(keyword)
    return word

## Define function to remove punctuation
def removePunct(xx):
    out = re.sub(r'[^\w\s]', ' ', xx)
    return out    


###  Punctuation
punct = set(string.punctuation)


def text_features(df):
    ### a. Make the original lower case and create a new column removing stopwords and punctuation
    df['JobText'] = df['JobText'].apply(lambda x: ' '.join([item.lower() for item in x.split()]))
    df['JobText'] = df['JobText'].apply(lambda x: removePunct(x))
    df['tokenize_jobtext']=df['JobText'].apply(nltk.word_tokenize)
    df['length'] = df.tokenize_jobtext.apply(lambda x: len(x))
    
    ### b. Apply count function 
    
    ### Wilmers and Zhang Dictionary
    df['wil_zha']= df.JobText.apply(lambda x: keyword_count(x, wil_zha_full))
    df['wil_zha_career']= df.JobText.apply(lambda x: keyword_count(x, wil_zha_career))
    df['wil_zha_life']= df.JobText.apply(lambda x: keyword_count(x, wil_zha_life))
    

    ### Intersection of Dictionaries
    df['main']=df.JobText.apply(lambda x: keyword_count(x, main))
    df['emp_ben']=df.JobText.apply(lambda x: keyword_count(x, emp_ben))
    df['values_purp']=df.JobText.apply(lambda x: keyword_count(x, values_purp))
    df['career']=df.JobText.apply(lambda x: keyword_count(x, career))
    df['worklife']=df.JobText.apply(lambda x: keyword_count(x, worklife))
    df['environ']=df.JobText.apply(lambda x: keyword_count(x, environ))
    df['gover']=df.JobText.apply(lambda x: keyword_count(x, gover))

    ### c. List of words
    df['words']= df.JobText.apply(lambda x: keyword_list(x, main))
    
    ### d. Date
    df['year'] = df.JobDate_x.apply(lambda x: x[0:4])
    df['month'] = df.JobDate_x.apply(lambda x: x[5:7])


    return df


### Apply text_features
    
### Create empty Dataframe
year=2021
df_year=pd.DataFrame()

### Declare path
path_txt=Path('/global/home/pc_moseguera/output/processed/'+str(year))

for file in path_txt.glob('*.csv'):
    print("Started working on file: " + file.name + " Time is: " + datetime.datetime.now().strftime("%H:%M:%S"))
    df_aux=pd.read_table(file, delimiter=',', header=0)
    df_aux = df_aux.dropna(subset = ['JobText'])

    train = pd.DataFrame()
    for i in range(16):
        print("Started processing: " + str(i*(100000)) + '. ' + 'Time is: ' + datetime.datetime.now().strftime("%H:%M:%S"))
        aux = parallelize_dataframe(df_aux.iloc[i*(100000):(100000)*(i+1)-1], text_features)
        train = train.append(aux)

    train.to_csv("../data/Burning Glass 2/final_variables/"+str(year)+"/full/full_" + file.name + ".zip", index = False, compression = "zip")
    train = train.drop(columns = ['JobText','JobText_pro','tokenize_jobtext'])
    train.to_csv("../data/Burning Glass 2/final_variables/"+str(year)+"/no_text/no_text_" + file.name + ".zip", index = False, compression = "zip")

    del train
    del df_aux
    del aux
    gc.collect()
    
