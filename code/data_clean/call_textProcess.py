from concurrent.futures import ProcessPoolExecutor
from textProcess import process_month_text

# Define input and output directories
input_base_directory = "/global/home/pc_moseguera/output/processed/"
output_base_directory = "/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/"

# Define the range of years to process
years = list(range(2017, 2022))  # Convert to list for parallel execution

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