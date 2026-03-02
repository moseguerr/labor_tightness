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

panel_main <- read_stata("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/job_wages2.dta")

########################################################################################################
###Variable transformation
########################################################################################################
log_sal=log(panel_main$MinSalary)
log_length=log(panel_main$length)
log_num_skills=log(panel_main$num_skills)
main_ratio=(panel_main$main/panel_main$length)*100
panel_main <- panel_main %>% mutate(college = 1*(Edu >= 16))
panel_main <- panel_main %>% mutate(partime = 1*(JobHours == 'parttime'))
panel_main <- panel_main %>% mutate(bonus_comm = 1*(SalaryType == 'bonus') + 1*(SalaryType =='commission'))

panel_main[panel_main == -999] <- NA
#########################################################################################################
###Regressions
#########################################################################################################

### 1a. Without controls
reg_1<-felm(log_sal ~ main_ratio | as.factor(year) | 0 | CanonEmployer, data=panel_main)
reg_2<-felm(log_sal ~ unemp_quarter:main_ratio+unemp_quarter+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA):as.factor(Sector)+as.factor(OccFam)+IsSpecialized  | 0 | CanonEmployer, data=panel_main)
reg_3<-felm(log_sal ~ unemp_quarter:main_ratio+unemp_quarter+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer)  | 0 | CanonEmployer, data=panel_main)
reg_4<-felm(log_sal ~ unemp_quarter:main_ratio+unemp_quarter+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year)  | 0 | CanonEmployer, data=panel_main)
reg_5<-felm(log_sal ~ tot_emp_log_change_nat:main_ratio+tot_emp_log_change_nat+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA):as.factor(Sector)+as.factor(OccFam)+IsSpecialized | 0 | CanonEmployer, data=panel_main)
reg_6<-felm(log_sal ~ tot_emp_log_change_nat:main_ratio+tot_emp_log_change_nat+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer) | 0 | CanonEmployer, data=panel_main)
reg_7<-felm(log_sal ~ tot_emp_log_change_nat:main_ratio+tot_emp_log_change_nat+main_ratio+college+log_num_skills+partime+bonus_comm | as.factor(year):as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(CanonEmployer):as.factor(year) | 0 | CanonEmployer, data=panel_main)

texreg(list(reg_1, reg_2, reg_3,reg_4, reg_5, reg_6, reg_7), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/wages_reg1.txt')

