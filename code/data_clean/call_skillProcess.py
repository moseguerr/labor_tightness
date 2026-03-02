#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 21:27:11 2025

@author: mgor
"""
import pandas as pd
import numpy as np
import re
import os
from concurrent.futures import ProcessPoolExecutor
from skillProcess import process_skill_files

# Define the years and directories
years = [str(year) for year in range(2010, 2012)]
main_directory = '/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Skill/'
base_output_directory = '/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'

# Define a wrapper function to process each year
def process_year(year):
    output_directory = os.path.join(base_output_directory, year)
    process_skill_files(year, main_directory, output_directory)
    return f"Year {year} processed."

# Use ProcessPoolExecutor to parallelize across 4 cores
if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_year, years))
    for result in results:
        print(result)
