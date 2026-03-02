import os
from mergeOther2 import process_files_for_year

# Define directories
years = [str(year) for year in range(2018, 2019)]
main_directory = '/global/home/pc_moseguera/data/Burning Glass 2/CSV/US/Add/Main/'
base_output_directory = '/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/'

if __name__ == "__main__":
    for year in years:  # ✅ Process years sequentially
        output_directory = os.path.join(base_output_directory, year)
        os.makedirs(output_directory, exist_ok=True)

        print(f"🔄 Starting processing for Year {year}...")
        process_files_for_year(year, main_directory, output_directory, max_workers=5)  # ✅ Parallelized within the year
        print(f"✅ Finished processing for Year {year}.")