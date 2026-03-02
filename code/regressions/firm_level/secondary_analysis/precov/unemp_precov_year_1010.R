#################################################################################################
### Load libraries
#################################################################################################
library(lubridate)
library(estimatr)
library(haven)
library(lfe)
library(dplyr)
library(texreg)

########################################################################################################
### Load data
#########################################################################################################

panel_main <- read_stata('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_firm_0406.dta')%>%
  filter(year<2020)

##########################################################################################################
#### Variable Transformation
##################################################################################################

log_length <- log(panel_main$length)
log_num_skills <- log(panel_main$num_skills)
panel_main[sapply(panel_main, is.infinite)] <- NA

# Calculate 25th percentile of unemployment across all states for each year
unemp_by_year <- panel_main %>%
  distinct(year, BestFitMSA, quarter, unemp_quarter) %>%
  group_by(year) %>%
  summarise(q25_unemp = quantile(unemp_quarter, probs = 0.25, na.rm = TRUE),
            q50_unemp = quantile(unemp_quarter, probs = 0.50, na.rm = TRUE),
            q75_unemp = quantile(unemp_quarter, probs = 0.75, na.rm = TRUE))

# Join the 25th percentile of unemployment to the original dataset
panel_main <- panel_main %>%
  left_join(unemp_by_year, by = "year")

# Create binary variable based on 25th percentile of unemployment in each year
panel_main <- panel_main %>%
    mutate(quartile_unemp = case_when(
    unemp_quarter < q25_unemp ~ 4,
    unemp_quarter >= q25_unemp & unemp_quarter < q50_unemp ~ 3,
    unemp_quarter >= q50_unemp & unemp_quarter < q75_unemp ~ 2,
    TRUE ~ 1))

panel_main <- panel_main %>%
  mutate(main_strict_ind = 100*(main_strict_ind),
         college = 100*college,
         parttime = 100*parttime,
         bon_com = 100*bon_com,
         main_mean_str = 100*(main_mean_str))

panel_main$quartile_unemp <- factor(panel_main$quartile_unemp, levels = c(1, 2, 3, 4))

##########################################################################################################
#### Regressions
##################################################################################################

reg_1 <- felm(main_strict_ind ~ as.factor(quartile_unemp) | as.factor(year) | 0 | Employer:BestFitMSA, data = panel_main)
reg_3 <- felm(main_strict_ind ~ as.factor(quartile_unemp) + college + parttime + bon_com | as.factor(BestFitMSA) + as.factor(year):as.factor(SOC):as.factor(Sector) + IsSpecialized | 0 | Employer, data = panel_main)
reg_4 <- felm(main_strict_ind ~ as.factor(quartile_unemp) + college + parttime + bon_com + logSize + gprofit + mlev + tonbiq + roe | as.factor(BestFitMSA) + as.factor(year):as.factor(SOC) + IsSpecialized + as.factor(Employer) | 0 | Employer, data = panel_main)
reg_5 <- felm(main_strict_ind ~ as.factor(quartile_unemp) + college + parttime + bon_com | as.factor(BestFitMSA) + as.factor(SOC) + IsSpecialized + as.factor(Employer):as.factor(year) | 0 | Employer, data = panel_main)

texreg(list(reg_1, reg_3, reg_4, reg_5), digits = 4, file = '/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/firm_level/secondary_analysis/precov/unemp_year_precov_1010.txt')
