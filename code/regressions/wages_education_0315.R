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
panel_main <- read_stata("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/job_wages.dta")


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

reg_1<-felm(log_sal ~ below25_unemp:main_ind+below25_unemp+main_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==1))
reg_2<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==1))
reg_3<-felm(log_sal ~ below25_unemp:values_purp_ind+below25_unemp+values_purp_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==1))
reg_4<-felm(log_sal ~ below25_unemp:emp_ben_ind+below25_unemp+emp_ben_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==1))
reg_5<-felm(log_sal ~ below25_unemp:main_ind+below25_unemp+main_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==0))
reg_6<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==0))
reg_7<-felm(log_sal ~ below25_unemp:values_purp_ind+below25_unemp+values_purp_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==0))
reg_8<-felm(log_sal ~ below25_unemp:emp_ben_ind+below25_unemp+emp_ben_ind+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+as.factor(CanonEmployer):as.factor(year)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset= (panel_main$college ==0))


texreg(list(reg_1, reg_2, reg_3, reg_4, reg_5, reg_6, reg_7, reg_8), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/quarter/wages_education_0315.txt')





