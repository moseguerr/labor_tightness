#!/bin/bash

#SBATCH --job-name=get_variables_2021  # create a job name
#SBATCH --partition=standard      # specify job partition
#SBATCH --mail-type=ALL           # email you when the job starts, stops, etc.
#SBATCH --mail-user=m.oseguera@rotman.utoronto.ca    # specify your email
#SBATCH --output=STD.out          # save standard output to STD.out
#SBATCH --error=STD.err           # save std. error output to STD.out
#SBATCH -c 12                      # request 4 CPUs
#SBATCH --time=12:00:00              # set total run time limit to 30mins (days-hrs:mins:secs)
#SBATCH --mem=12000                # request 5G memory

module load anaconda/3.6        # load python module
python3 get_final_variables_df_2021.py             # run python code