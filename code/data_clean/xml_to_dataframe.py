# Libraries
import pandas as pd
import xml.etree.ElementTree as ET
import os
import time
import gc
from zipfile import ZipFile
from multiprocessing import Pool
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Create functions

def xmlToDF_incremental(filePath, vvars):
    """
    Parse XML incrementally and convert it to DataFrame.
    """
    outObs = []
    for event, elt in ET.iterparse(filePath, events=('end',)):
        if elt.tag == 'Job':  # Replace 'Job' with the correct XML root element for your data
            aux = []
            for vv in vvars:
                child = elt.find(vv)
                aux.append(child.text if child is not None else None)
            outObs.append(aux)
            elt.clear()  # Clear memory for processed elements
    return pd.DataFrame(outObs, columns=vvars)

def processFile(fileName, route, destination, vvars):
    """
    Process a single file: unzip, parse incrementally, and save results in Parquet format.
    """
    try:
        zipPath = f"{route}{fileName}.zip"
        print(f"Unzipping file: {zipPath}")
        with ZipFile(zipPath, 'r') as zip_ref:
            zip_ref.extractall('../temp')
        
        xmlPath = f"../temp/{fileName}.xml"
        print(f"Parsing XML file: {xmlPath}")
        df = xmlToDF_incremental(xmlPath, vvars)
        
        if df.empty:
            logging.warning(f"No data extracted from file: {fileName}")
            return
        
        # Save as Parquet
        parquetPath = f"{destination}{fileName}.parquet"
        print(f"Saving Parquet file: {parquetPath}")
        df.to_parquet(parquetPath, index=False)  # No need to specify engine unless debugging
        
        # Clean up
        os.remove(xmlPath)
        logging.info(f"Processed file: {fileName}")
    except Exception as e:
        logging.error(f"Error processing file {fileName}: {e}")
        raise

def main():
    # Specify the range of years
    years = range(2013, 2023)  # 2023 is exclusive, so it includes 2013-2022
    n_cores = 9  # Specify the number of cores to use
    
    # Set paths
    mainRoute = '/global/home/pc_moseguera/code/'
    os.chdir(mainRoute)
    
    # Iterate over each year
    for year in years:
        print(f"Processing year: {year}")
        dataRoute = f'../data/Burning Glass 2/Jobs/US/Add/{year}/'
        destinationRoute = f'../output/processed/{year}/'
        os.makedirs(destinationRoute, exist_ok=True)
        
        # Get the list of all files in the specified year directory
        if not os.path.exists(dataRoute):
            logging.warning(f"Data directory does not exist for year {year}: {dataRoute}")
            continue
        
        fileList = [x[:-4] for x in os.listdir(dataRoute)]  # Remove .zip extensions
        
        # Get the list of already processed files
        alreadyList = [x[:-8] for x in os.listdir(destinationRoute)]  # Remove .parquet extensions
        remainingFiles = [ff for ff in fileList if ff not in alreadyList]
        
        # Set variables to extract
        vvars = ['JobID', 'CanonEmployer', 'JobReferenceID', 'JobDate', 'JobText', 'IsDuplicate', 'IsDuplicateOf']
        
        # Process files in parallel
        with Pool(processes=n_cores) as pool:
            pool.starmap(processFile, [(file, dataRoute, destinationRoute, vvars) for file in remainingFiles])
        
        logging.info(f"Finished processing year: {year}")

# Run the script
if __name__ == "__main__":
    main()
