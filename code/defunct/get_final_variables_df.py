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

### Set paths
os.chdir("/global/home/pc_moseguera/code")

### Read Table 
df_2022=pd.read_table('../data/Burning Glass 2/Processed/merged_2022.zip', delimiter=',', header=0)

### Read dictionaries
df_dict=pd.read_table('../data/Burning Glass 2/Processed/dictionaries.csv', delimiter=',', header=0)

full_list=df_dict.wilmers_zhang_main.str.strip().str.replace('_', ' ').dropna().tolist()
career_meaning=df_dict.wilmers_zhang_career.str.strip().str.replace('_', ' ').dropna().tolist()
worklife_meaning=df_dict.wilmers_zhang_life.str.strip().str.replace('_', ' ').dropna().tolist()
SDG_dict=df_dict.amel_etal.str.strip().str.replace('_', ' ').dropna().tolist()
pema=df_dict.pencle_malanescu.str.strip().str.replace('_', ' ').dropna().tolist()
banks=df_dict.banks.str.strip().str.replace('_', ' ').dropna().tolist()
main_dict=df_dict.main.str.strip().str.replace('_', ' ').dropna().tolist()

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

## Define function to remove punctuation
def removePunct(xx):
    out = re.sub(r'[^\w\s]', '', xx)
    return out    


### Define stopwords and punctuation
stopwords=sw.words("english")
stopwords= stopwords+['apply', 'job','jobs', 'sales'] ##Remove other common words
punct = set(string.punctuation)


def text_features(df):
    ### a. Make the original lower case and create a new column removing stopwords and punctuation
    df['JobText'] = df['JobText'].apply(lambda x: ' '.join([item.lower() for item in x.split()]))
    df['JobText'] = df['JobText'].apply(lambda x: removePunct(x))
    df['JobText_pro'] = df['JobText'].apply(lambda x: ' '.join([item.lower() for item in x.split() if item not in stopwords]))
    df['tokenize_jobtext']=df['JobText_pro'].apply(nltk.word_tokenize)
    df['length'] = df.tokenize_jobtext.apply(lambda x: len(x))
    
    ### Creating list of frequencies 
    df['WordFreq']=df['tokenize_jobtext'].apply(nltk.FreqDist)
    
    ### Most Common Word
    #Changed this line
    df['MostCom'] = df.WordFreq.apply(lambda x: x.most_common(1) if len(x.most_common(1)) > 0 else [("",0)])
    
    ### Separate Most Common Word into Word and Frequency + Relative Frequency 
    df['ComWord']=df['MostCom'].apply(lambda x: x[0][0])
    df['Freq']=df['MostCom'].apply(lambda x: x[0][1])
    df['Rel_Freq']=df['Freq']/df['length']
    
    ### Apply count function 
    
    ### Wilmers and Zhang Dictionary
    df['Full_wilzha']= df.JobText.apply(lambda x: keyword_count(x, full_list))/df['length']
    df['career_meaning']= df.JobText.apply(lambda x: keyword_count(x, career_meaning))/df['length']
    df['worklife_meaning']= df.JobText.apply(lambda x: keyword_count(x, worklife_meaning))/df['length']
    
    ###  Amel-Zadeh et al (2021) SDGs Dictionary
    df['SDGs']=df.JobText.apply(lambda x: keyword_count(x, SDG_dict))/df['length']
    
    ### Pencle & Mălăescu (2016)– Corporate Social Responsibility
    df['CSR']=df.JobText.apply(lambda x: keyword_count(x, pema))/df['length']
    
    ### Banks–Recruiting Signals of CSR, Development, Wellness, Inclusiveness
    df['Recru_sig']=df.JobText.apply(lambda x: keyword_count(x, banks))/df['length']
    
    ### Intersection
    df['main_dict']=df.JobText.apply(lambda x: keyword_count(x, main_dict))/df['length']
    
    ## Date
    df['year'] = df.JobDate_x.apply(lambda x: x[0:4])
    df['month'] = df.JobDate_x.apply(lambda x: x[5:7])


    return df


### Apply text_features
    
### Create empty Dataframe
df_2021=pd.DataFrame()

### Declare path
path_txt=Path('/global/home/pc_moseguera/output/processed/2021')

for file in path_txt.glob('*.csv'):
    print("Started working on file: " + file.name + " Time is: " + datetime.datetime.now().strftime("%H:%M:%S"))
    df_aux=pd.read_table(file, delimiter=',', header=0)
    df_aux = df_aux.dropna(subset = ['JobText'])
        
    train = pd.DataFrame()
    for i in range(16):
        print("Started processing: " + str(i*(100000)) + '. ' + 'Time is: ' + datetime.datetime.now().strftime("%H:%M:%S"))
        aux = parallelize_dataframe(df_aux.iloc[i*(100000):(100000)*(i+1)-1], text_features)
        train = train.append(aux)
        
    df_2021=df_2021.append(train)
    
    del train
    del df_aux
    del aux
    
df_2021.to_csv("../data/Burning Glass 2/final_variables/full_2021.csv", index = False, compression = "zip")

df_2021 = df_2021.drop(columns = ['JobText','JobText_pro','tokenize_jobtext'])

df_2021.to_csv("../data/Burning Glass 2/final_variables/no_text_2021.csv", index = False, compression = "zip")
