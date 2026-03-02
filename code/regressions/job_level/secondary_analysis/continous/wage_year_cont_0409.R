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
panel_main <- read_stata('/Volumes/TOSHIBA EXT/Second Year Paper/test/panel_jobcomp_0406.dta')
########################################################################################################
###Variable transformation
########################################################################################################
log_sal=log(panel_main$MinSalary)
log_length=log(panel_main$length)
log_num_skills=log(panel_main$num_skills)


# Calculate 25th percentile of unemployment across all states for each year
unemp_by_year <- panel_main %>%
  distinct(year, BestFitMSA, quarter, unemp_quarter) %>%
  group_by(year) %>%
  summarise(q25_unemp = quantile(unemp_quarter, probs = 0.25, na.rm = TRUE))

# Join the 25th percentile of unemployment to the original dataset
panel_main <- panel_main %>%
  left_join(unemp_by_year, by = "year")

# Create binary variable based on 25th percentile of unemployment in each year
panel_main <- panel_main %>%
  mutate(below25_unemp = ifelse(unemp_quarter < q25_unemp, 1, 0))

#########################################################################################################
###Regressions
#########################################################################################################
###Using main_strict_ind

reg_1<-felm(log_sal ~ main_strict+below25_unemp | as.factor(year) | 0 | Employer, data=panel_main)
reg_2<-felm(log_sal ~ below25_unemp:main_strict+below25_unemp+main_strict+college+parttime+bon_com | as.factor(year):as.factor(OccFam)+as.factor(BestFitMSA)+IsSpecialized | 0 | Employer, data=panel_main)
reg_3<-felm(log_sal ~ below25_unemp:main_strict+below25_unemp+main_strict+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+as.factor(Sector)+IsSpecialized  | 0 | Employer, data=panel_main)
reg_4<-felm(log_sal ~ below25_unemp:main_strict+below25_unemp+main_strict+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(OccFam):+as.factor(Sector):as.factor(year)+IsSpecialized  | 0 | Employer, data=panel_main)

                          
texreg(list(reg_1, reg_2, reg_3, reg_4), digits =4, file='/Volumes/TOSHIBA EXT/Second Year Paper/Regression Tables/job_level/secondary_analysis/continous/wage_year_cont_0508.txt')
                          
                          