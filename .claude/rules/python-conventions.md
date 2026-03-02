# Python Conventions

## Data Pipeline

- Data cleaning scripts run on **Georgetown MDI GPU Cluster** (Linux)
- Server paths start with `/global/home/pc_moseguera/data/`
- Use `pandas` for data manipulation, `pyarrow`/`fastparquet` for parquet I/O
- Limit threading: set `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`
- Use `gc.collect()` after processing large DataFrames
- Convert object columns to `category` dtype for memory efficiency

## NLP Pipeline

- `refine_dictionaries.py` uses KeyBERT + SentenceTransformers for dictionary expansion
- Cosine similarity threshold: 0.7 for matching new terms to categories
- Dictionary categories: meaningful_work, environmental_initiatives, social_initiatives (core); organizational_culture (partial); pecuniary_benefits, job_design, career_dev, job_tasks (excluded/controls)

## Style

- No type annotations unless they clarify complex signatures
- Prefer explicit over clever
- Comments where logic isn't self-evident
