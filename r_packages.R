# R packages required for regression analysis
# Install: source("r_packages.R")

packages <- c(
  "lfe",          # Fixed effects linear models (felm)
  "estimatr",     # Robust standard errors
  "haven",        # Read Stata .dta files
  "texreg",       # Regression tables (screenreg, texreg)
  "dplyr",        # Data manipulation
  "lubridate",    # Date handling
  "tidyr",        # Data reshaping
  "ggplot2",      # Plotting
  "stargazer"     # Alternative regression tables
)

install_if_missing <- function(pkg) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

invisible(lapply(packages, install_if_missing))
cat("All packages installed.\n")
