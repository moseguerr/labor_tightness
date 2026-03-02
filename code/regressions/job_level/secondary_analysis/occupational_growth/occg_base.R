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
panel_main <- read_stata("/Volumes/TOSHIBA EXT/Second Year Paper/test/panel_jobcomp_0406.dta")


########################################################################################################
###Variable transformation
########################################################################################################
log_sal=log(panel_main$MinSalary)
log_length=log(panel_main$length)
log_num_skills=log(panel_main$num_skills)


panel_main<-panel_main %>% 
  mutate(below25_unemp = 1*(unemp_quarter < quantile(unemp_quarter, probs = 0.25, na.rm = T))) %>% 
  ungroup()

#########################################################################################################
###Regressions
#########################################################################################################
### 1a. Low Unemployment


reg_1<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==0))
reg_2<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==0))
reg_3<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==1))
reg_4<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==1))

reg_5<-felm(log_sal ~ below25_unemp:main_mean_str+below25_unemp+main_mean_str+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==0))
reg_6<-felm(log_sal ~ below25_unemp:main_mean_str+below25_unemp+main_mean_str+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==0))
reg_7<-felm(log_sal ~ below25_unemp:main_mean_str+below25_unemp+main_mean_str+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==1))
reg_8<-felm(log_sal ~ below25_unemp:main_mean_str+below25_unemp+main_mean_str+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year)  | 0 | Employer, data=panel_main, subset= (panel_main$occ_mean ==1))

texreg(list(reg_1, reg_2, reg_3, reg_4), digits =4, file='/Volumes/TOSHIBA EXT/Second Year Paper/Regression Tables/job_level/secondary_analysis/occupation_growth/main_occ_base.txt')

texreg(list(reg_5, reg_6, reg_7, reg_8), digits =4, file='/Volumes/TOSHIBA EXT/Second Year Paper/Regression Tables/job_level/secondary_analysis/occupation_growth/mean_occ_base.txt')




