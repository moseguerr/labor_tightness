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
  group_by(year) %>% 
  mutate(below25_unemp = 1*(Unemployment_Rate < quantile(Unemployment_Rate, probs = 0.25, na.rm = T))) %>% 
  ungroup()

panel_main<-panel_main %>% 
  group_by(year) %>% 
  mutate(above75_emp = 1*(tot_emp_log_change_nat > quantile(tot_emp_log_change_nat, probs = 0.75, na.rm = T))) %>% 
  ungroup()
#########################################################################################################
###Regressions
#########################################################################################################
### 1a. Low Unemployment


reg_1<-felm(log_sal ~ main_strict_ind | as.factor(year) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_2<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(year):as.factor(OccFam):as.factor(Sector)+as.factor(BestFitMSA)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_3<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer)  | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_4<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year)  | 0 | CanonEmployer, data=panel_main,subset=panel_main$less_45 ==0)
reg_5<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com| as.factor(year):as.factor(BestFitMSA):as.factor(Sector)+as.factor(OccFam)+IsSpecialized | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_6<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_7<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)

reg_8<-felm(log_sal ~ main_strict_ind | as.factor(year) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_9<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(year):as.factor(OccFam):as.factor(Sector)+as.factor(BestFitMSA)+IsSpecialized  | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_10<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer)  | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_11<-felm(log_sal ~ below25_unemp:main_strict_ind+below25_unemp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year)  | 0 | CanonEmployer, data=panel_main,subset=panel_main$less_45 ==0)
reg_12<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com| as.factor(year):as.factor(BestFitMSA):as.factor(Sector)+as.factor(OccFam)+IsSpecialized | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_13<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)
reg_14<-felm(log_sal ~ above75_emp:main_strict_ind+above75_emp+main_strict_ind+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year) | 0 | CanonEmployer, data=panel_main, subset=panel_main$less_45 ==0)

texreg(list(reg_1, reg_2, reg_3,reg_4, reg_5, reg_6, reg_7), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/wages_reg_more45.txt')
texreg(list(reg_8, reg_9, reg_10,reg_11, reg_12, reg_13, reg_14), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/wages_reg_less45.txt')


