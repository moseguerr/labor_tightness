#################################################################################################
### Bartik IV Wage Regressions
### Instruments MSA-level unemployment with shift-share Bartik instrument
### Following BHJ (2022) framework with JRS (2018) dynamic control
#################################################################################################

library(lubridate)
library(estimatr)
library(haven)
library(lfe)
library(dplyr)
library(texreg)
library(arrow)

########################################################################################################
### Load data
#########################################################################################################

# Job-level wage data
panel_main <- read_stata("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/job_wages.dta")

# Bartik instrument (parquet)
bartik <- read_parquet("data/bartik/bartik_instrument.parquet")

########################################################################################################
### Variable transformation
########################################################################################################
log_sal <- log(panel_main$MinSalary)
log_length <- log(panel_main$length)
log_num_skills <- log(panel_main$num_skills)

# Compute quarter from month if not already present
if (!"qtr" %in% names(panel_main)) {
  if ("month" %in% names(panel_main)) {
    panel_main$qtr <- ceiling(panel_main$month / 3)
  } else if ("quarter" %in% names(panel_main)) {
    panel_main$qtr <- panel_main$quarter
  }
}

########################################################################################################
### Merge Bartik instrument
########################################################################################################

# BestFitMSA in regressions is 4-digit QCEW code; bartik has BestFitMSA4 (same format)
bartik_merge <- bartik %>%
  select(BestFitMSA4, year, qtr, bartik, bartik_no611, bartik_lag4)

panel_main <- panel_main %>%
  left_join(bartik_merge,
            by = c("BestFitMSA" = "BestFitMSA4", "year", "qtr"))

cat("Bartik merge coverage:\n")
cat("  Total obs:", nrow(panel_main), "\n")
cat("  With bartik:", sum(!is.na(panel_main$bartik)), "\n")
cat("  With bartik_lag4:", sum(!is.na(panel_main$bartik_lag4)), "\n")

########################################################################################################
### Define tightness (continuous unemployment rate for IV)
########################################################################################################

# For IV: use continuous unemployment rate as endogenous variable
# below25_unemp is derived from it; we instrument unemp_quarter with bartik

# Also create the binary variable for comparison with OLS
unemp_by_year <- panel_main %>%
  distinct(year, BestFitMSA, qtr, unemp_quarter) %>%
  group_by(year) %>%
  summarise(q25_unemp = quantile(unemp_quarter, probs = 0.25, na.rm = TRUE))

panel_main <- panel_main %>%
  left_join(unemp_by_year, by = "year") %>%
  mutate(below25_unemp = ifelse(unemp_quarter < q25_unemp, 1, 0))

########################################################################################################
### PANEL A: First Stage — Bartik predicts unemployment rate
### (Reported in paper to show instrument relevance)
########################################################################################################

cat("\n=== FIRST STAGE: Bartik → Unemployment Rate ===\n")

# Col 1: Baseline (year FE only)
fs_1 <- felm(unemp_quarter ~ bartik
              | as.factor(year)
              | 0
              | BestFitMSA,
              data = panel_main)

# Col 2: + Occupation×Year + MSA FE
fs_2 <- felm(unemp_quarter ~ bartik + college + parttime
              | as.factor(year):as.factor(OccFam) + as.factor(BestFitMSA) + IsSpecialized
              | 0
              | BestFitMSA,
              data = panel_main)

# Col 3: + Firm FE
fs_3 <- felm(unemp_quarter ~ bartik + college + parttime
              | as.factor(BestFitMSA) + as.factor(year):as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer)
              | 0
              | BestFitMSA,
              data = panel_main)

# Col 4: Firm×Year FE
fs_4 <- felm(unemp_quarter ~ bartik + college + parttime
              | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
              | 0
              | BestFitMSA,
              data = panel_main)

# Col 5: JRS dynamic control (include bartik_lag4)
fs_5 <- felm(unemp_quarter ~ bartik + bartik_lag4 + college + parttime
              | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
              | 0
              | BestFitMSA,
              data = panel_main)

texreg(list(fs_1, fs_2, fs_3, fs_4, fs_5), digits = 4,
       custom.model.names = c("(1)", "(2)", "(3)", "(4)", "(5) JRS"),
       file = "data/bartik/tables/first_stage.txt")

cat("First stage saved to data/bartik/tables/first_stage.txt\n")

########################################################################################################
### PANEL B: 2SLS — Log wages instrumented
### Main specification: instrument unemp_quarter with bartik
########################################################################################################

cat("\n=== 2SLS: Wages ~ Purpose × Unemployment (instrumented) ===\n")

# ── Primary: Instrument continuous unemployment ─────────────────────────

# Col 1: OLS baseline for comparison (year FE only)
ols_1 <- felm(log_sal ~ main_strict_ind*unemp_quarter
               | as.factor(year)
               | 0
               | CanonEmployer,
               data = panel_main)

# Col 2: 2SLS (year FE only)
iv_1 <- felm(log_sal ~ main_strict_ind
              | as.factor(year)
              | (unemp_quarter ~ bartik)
              | CanonEmployer,
              data = panel_main)

# Col 3: 2SLS + controls + FE
iv_2 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
              | as.factor(year):as.factor(OccFam) + as.factor(BestFitMSA) + IsSpecialized
              | (unemp_quarter ~ bartik)
              | CanonEmployer,
              data = panel_main)

# Col 4: 2SLS + Firm FE
iv_3 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
              | as.factor(BestFitMSA) + as.factor(year):as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer)
              | (unemp_quarter ~ bartik)
              | CanonEmployer,
              data = panel_main)

# Col 5: 2SLS + Firm×Year FE
iv_4 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
              | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
              | (unemp_quarter ~ bartik)
              | CanonEmployer,
              data = panel_main)

texreg(list(ols_1, iv_1, iv_2, iv_3, iv_4), digits = 4,
       custom.model.names = c("OLS", "IV (1)", "IV (2)", "IV (3)", "IV (4)"),
       file = "data/bartik/tables/wages_iv_main.txt")

cat("2SLS main results saved to data/bartik/tables/wages_iv_main.txt\n")

########################################################################################################
### PANEL C: 2SLS with interaction — Purpose × Unemployment (instrumented)
### The key causal test: does purpose × tightness → higher wages?
########################################################################################################

cat("\n=== 2SLS WITH INTERACTION: Purpose × Instrumented Tightness ===\n")

# For the interaction, we instrument both unemp_quarter and
# unemp_quarter:main_strict_ind using bartik and bartik:main_strict_ind

# Col 1: OLS with interaction (binary tightness)
ols_int <- felm(log_sal ~ below25_unemp:main_strict_ind + below25_unemp + main_strict_ind + college + parttime + bon_com
                | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                | 0
                | CanonEmployer,
                data = panel_main)

# Col 2: IV with interaction (continuous unemployment)
# Instrument unemp_quarter and unemp_quarter×main_strict_ind
# using bartik and bartik×main_strict_ind
panel_main$unemp_x_purpose <- panel_main$unemp_quarter * panel_main$main_strict_ind
panel_main$bartik_x_purpose <- panel_main$bartik * panel_main$main_strict_ind

iv_int_1 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                  | as.factor(year):as.factor(OccFam) + as.factor(BestFitMSA) + IsSpecialized
                  | (unemp_quarter | unemp_x_purpose ~ bartik + bartik_x_purpose)
                  | CanonEmployer,
                  data = panel_main)

# Col 3: IV interaction + Firm FE
iv_int_2 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                  | as.factor(BestFitMSA) + as.factor(year):as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer)
                  | (unemp_quarter | unemp_x_purpose ~ bartik + bartik_x_purpose)
                  | CanonEmployer,
                  data = panel_main)

# Col 4: IV interaction + Firm×Year FE
iv_int_3 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                  | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                  | (unemp_quarter | unemp_x_purpose ~ bartik + bartik_x_purpose)
                  | CanonEmployer,
                  data = panel_main)

texreg(list(ols_int, iv_int_1, iv_int_2, iv_int_3), digits = 4,
       custom.model.names = c("OLS", "IV (1)", "IV (2)", "IV (3)"),
       file = "data/bartik/tables/wages_iv_interaction.txt")

cat("2SLS interaction results saved to data/bartik/tables/wages_iv_interaction.txt\n")

########################################################################################################
### PANEL D: JRS Dynamic Control Robustness
### Include bartik_lag4 as additional instrument to control for serial correlation
########################################################################################################

cat("\n=== JRS DYNAMIC CONTROL ROBUSTNESS ===\n")

# Subset to obs with lagged instrument
panel_jrs <- panel_main %>% filter(!is.na(bartik_lag4))
panel_jrs$bartik_lag4_x_purpose <- panel_jrs$bartik_lag4 * panel_jrs$main_strict_ind

cat("JRS subsample:", nrow(panel_jrs), "obs (vs", nrow(panel_main), "full)\n")

# Col 1: JRS — instrument unemp with (bartik, bartik_lag4)
iv_jrs_1 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com + bartik_lag4
                  | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                  | (unemp_quarter ~ bartik + bartik_lag4)
                  | CanonEmployer,
                  data = panel_jrs)

# Col 2: JRS with interaction
iv_jrs_2 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com + bartik_lag4 + bartik_lag4_x_purpose
                  | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                  | (unemp_quarter | unemp_x_purpose ~ bartik + bartik_x_purpose + bartik_lag4 + bartik_lag4_x_purpose)
                  | CanonEmployer,
                  data = panel_jrs)

texreg(list(iv_jrs_1, iv_jrs_2), digits = 4,
       custom.model.names = c("JRS Main", "JRS Interaction"),
       file = "data/bartik/tables/wages_iv_jrs.txt")

cat("JRS robustness saved to data/bartik/tables/wages_iv_jrs.txt\n")

########################################################################################################
### PANEL E: No-NAICS-611 Robustness
### Show results not driven by education sector shocks
########################################################################################################

cat("\n=== NO-NAICS-611 ROBUSTNESS ===\n")

panel_main$bartik_no611_x_purpose <- panel_main$bartik_no611 * panel_main$main_strict_ind

# Col 1: No-611 instrument
iv_no611_1 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                    | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                    | (unemp_quarter ~ bartik_no611)
                    | CanonEmployer,
                    data = panel_main)

# Col 2: No-611 with interaction
iv_no611_2 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                    | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                    | (unemp_quarter | unemp_x_purpose ~ bartik_no611 + bartik_no611_x_purpose)
                    | CanonEmployer,
                    data = panel_main)

texreg(list(iv_no611_1, iv_no611_2), digits = 4,
       custom.model.names = c("No-611 Main", "No-611 Interaction"),
       file = "data/bartik/tables/wages_iv_no611.txt")

cat("No-611 robustness saved to data/bartik/tables/wages_iv_no611.txt\n")

########################################################################################################
### PANEL F: Oster (2019) Coefficient Stability
### Progressive control saturation — show coefficient stability
########################################################################################################

cat("\n=== OSTER (2019) COEFFICIENT STABILITY ===\n")

# OLS specifications with increasing controls
stab_1 <- felm(log_sal ~ main_strict_ind*unemp_quarter
                | as.factor(year)
                | 0
                | CanonEmployer,
                data = panel_main)

stab_2 <- felm(log_sal ~ unemp_quarter:main_strict_ind + unemp_quarter + main_strict_ind + college + parttime + bon_com
                | as.factor(year):as.factor(OccFam) + as.factor(BestFitMSA) + IsSpecialized
                | 0
                | CanonEmployer,
                data = panel_main)

stab_3 <- felm(log_sal ~ unemp_quarter:main_strict_ind + unemp_quarter + main_strict_ind + college + parttime + bon_com
                | as.factor(BestFitMSA) + as.factor(year):as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer)
                | 0
                | CanonEmployer,
                data = panel_main)

stab_4 <- felm(log_sal ~ unemp_quarter:main_strict_ind + unemp_quarter + main_strict_ind + college + parttime + bon_com
                | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                | 0
                | CanonEmployer,
                data = panel_main)

# IV specification (preferred)
stab_5 <- felm(log_sal ~ main_strict_ind + college + parttime + bon_com
                | as.factor(BestFitMSA) + as.factor(OccFam) + IsSpecialized + as.factor(CanonEmployer):as.factor(year)
                | (unemp_quarter | unemp_x_purpose ~ bartik + bartik_x_purpose)
                | CanonEmployer,
                data = panel_main)

texreg(list(stab_1, stab_2, stab_3, stab_4, stab_5), digits = 4,
       custom.model.names = c("OLS (1)", "OLS (2)", "OLS (3)", "OLS (4)", "IV"),
       file = "data/bartik/tables/coefficient_stability.txt")

cat("Coefficient stability table saved to data/bartik/tables/coefficient_stability.txt\n")

########################################################################################################
### Summary diagnostics
########################################################################################################

cat("\n=== IV DIAGNOSTICS SUMMARY ===\n")

# Print first-stage F statistics
cat("\nFirst-stage F statistics (from felm):\n")
for (i in 1:5) {
  model <- get(paste0("fs_", i))
  cat("  FS Col", i, ": coef =", round(coef(model)["bartik"], 4),
      ", se =", round(summary(model)$coefficients["bartik", "Cluster s.e."], 4), "\n")
}

# Print key IV coefficients
cat("\nKey IV coefficients (unemp_quarter on log_sal):\n")
cat("  IV main (no interaction):", round(coef(iv_4)["unemp_quarter(fit)"], 4), "\n")

cat("\n=== DONE ===\n")
