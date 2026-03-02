from textProcess import process_month_text
from concurrent.futures import ProcessPoolExecutor
import logging

# Setup logging
log_file = "error_log_2021.txt"
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the range of years to process
years = list(range(2021, 2022))  # Convert to list for parallel execution

def process_wrapper(year):
    """Wrapper function to handle errors in parallel execution."""
    try:
        print(f"Processing year {year}...")
        process_month_text(year, input_base_directory, output_base_directory)
        print(f"Finished processing year {year}.")
        return f"Completed: {year}"
    except Exception as e:
        print(f"Error processing {year}: {e}")
        return f"Failed: {year}"

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as executor:  # 🔹 Reduce workers to prevent memory overload
        results = list(executor.map(process_wrapper, years))

    for result in results:
        print(result)