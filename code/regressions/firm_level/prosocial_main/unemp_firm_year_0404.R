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

panel_main <- read_stata('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_firm_0403.dta') 

##########################################################################################################
#### Variable Transformation
##################################################################################################

log_length=log(panel_main$length)
log_num_skills=log(panel_main$num_skills)
panel_main[sapply(panel_main, is.infinite)] <- NA


panel_main<-panel_main %>% 
  group_by(year) %>%
  mutate(below25_unemp = 1*(unemp_quarter < quantile(unemp_quarter, probs = 0.25, na.rm = T))) %>% 
  ungroup()

panel_main<-panel_main %>%
  group_by(year) %>%
  mutate(above75_unemp = 1*(unemp_quarter > quantile(unemp_quarter, probs = 0.75, na.rm = T))) %>% 
  ungroup()

panel_main<-panel_main %>% 
  mutate(main_strict_ind = 100*(main_strict_ind),
         college=100*college,
         parttime=100*parttime,
         bon_com=100*bon_com,
         main_mean_str = 100*(main_mean_str)) 

##########################################################################################################
#### Regressions
##################################################################################################

reg_1<-felm(main_mean_str~ below25_unemp | as.factor(year)| 0 |Employer:BestFitMSA, data=panel_main)
reg_2<-felm(main_mean_str~ below25_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_3<-felm(main_mean_str~ below25_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_4<-felm(main_mean_str~ below25_unemp+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_5<-felm(main_mean_str~ below25_unemp+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

reg_6<-felm(main_mean_str~ above75_unemp | as.factor(year)| 0 |Employer, data=panel_main)
reg_7<-felm(main_mean_str~ above75_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_8<-felm(main_mean_str~ above75_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_9<-felm(main_mean_str~ above75_unemp+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_10<-felm(main_mean_str~above75_unemp+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

texreg(list(reg_1, reg_2, reg_3, reg_4, reg_5, reg_6, reg_7, reg_8, reg_9, reg_10), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_year_firm_mean.txt')

reg_1<-felm(main_strict_ind~ below25_unemp | as.factor(year)| 0 |Employer:BestFitMSA, data=panel_main)
reg_2<-felm(main_strict_ind~ below25_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_3<-felm(main_strict_ind~ below25_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_4<-felm(main_strict_ind~ below25_unemp+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_5<-felm(main_strict_ind~ below25_unemp+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

reg_6<-felm(main_strict_ind~ above75_unemp | as.factor(year)| 0 |Employer, data=panel_main)
reg_7<-felm(main_strict_ind~ above75_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_8<-felm(main_strict_ind~ above75_unemp+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_9<-felm(main_strict_ind~ above75_unemp+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_10<-felm(main_strict_ind~above75_unemp+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )


texreg(list(reg_1, reg_2, reg_3, reg_4, reg_5, reg_6, reg_7, reg_8, reg_9, reg_10), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_year_firm_main.txt')
