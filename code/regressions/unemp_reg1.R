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

panel_main <- read.csv(unz("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_emp.zip", "panel_emp.csv"), header = TRUE,
                       sep = ",") 
##########################################################################################################
#### Variable Transformation
##################################################################################################

log_length=log(panel_main$length)
log_num_skills=log(panel_main$num_skills)
main_ratio=(panel_main$main/panel_main$length)*100
panel_main[sapply(panel_main, is.infinite)] <- NA


##########################################################################################################
#### Regressions
##################################################################################################
reg_1<-felm(main_ind ~ Unemployment.Rate | as.factor(year) | 0 |Employer, data=panel_main)
reg_2<-felm(main_ind ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_3<-felm(main_ind ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_4<-felm(main_ind ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length| as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )


reg_5<-felm(main_mean ~ Unemployment.Rate | as.factor(year) | 0 |Employer, data=panel_main)
reg_6<-felm(main_mean ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_7<-felm(main_mean ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_8<-felm(main_mean ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+log_length | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

reg_9<-felm(main_ratio ~ Unemployment.Rate | as.factor(year) | 0 |Employer, data=panel_main)
reg_10<-felm(main_ratio ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills |as.factor(BestFitMSA)+ as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_11<-felm(main_ratio ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam):as.factor(Sector)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_12<-felm(main_ratio ~ Unemployment.Rate+college+parttime+bon_com+log_num_skills | as.factor(BestFitMSA)+as.factor(year):as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )


texreg(list(reg_1, reg_2, reg_3,reg_4), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_reg1.txt')
texreg(list(reg_5, reg_6, reg_7, reg_8), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_reg2.txt')
texreg(list( reg_9, reg_10, reg_11, reg_12), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_reg3.txt')

