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

filePath<-'/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/all_years_dta/'
currFile <- paste0(filePath,'panel_emp2010.dta')
panel_main <- read_stata(currFile)


# Loop years
yearList <- 2011:2021

for(yyyy in yearList){
  currFile <- paste0(filePath,'panel_emp',yyyy,'.dta')
  dfCurr <- read_stata(currFile)
  dfCurr <- dfCurr %>% select(-'_merge') 
  panel_main <- panel_main %>% 
    bind_rows(dfCurr)
}

#panel_main <- read.csv(unz("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_emp.zip", "panel_emp.csv"), header = TRUE,sep = ",") 
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

reg_1<-felm(main_mean ~ Unemployment_Rate | as.factor(year)| 0 |Employer, data=panel_main)
reg_2<-felm(main_mean ~ Unemployment_Rate+college+parttime+bon_com |as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_3<-felm(main_mean ~ Unemployment_Rate+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_4<-felm(main_mean ~ Unemployment_Rate+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

reg_5<-felm(main_ratio ~ Unemployment_Rate |as.factor(year)| 0 |Employer, data=panel_main)
reg_6<-felm(main_ratio ~ Unemployment_Rate+college+parttime+bon_com |as.factor(BestFitMSA)+ as.factor(year)+as.factor(OccFam)+as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_7<-felm(main_ratio ~ Unemployment_Rate+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_8<-felm(main_ratio ~ Unemployment_Rate+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )


texreg(list(reg_1, reg_2, reg_3, reg_4), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_reg1.txt')
texreg(list( reg_5, reg_6, reg_7, reg_8), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/unemp_reg2.txt')

reg_9<-felm(main_mean ~ tot_emp_log_change_nat | as.factor(year) | 0 |Employer, data=panel_main)
reg_10<-felm(main_mean ~ tot_emp_log_change_nat+college+parttime+bon_com |as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+ as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_11<-felm(main_mean ~ tot_emp_log_change_nat+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_12<-felm(main_mean ~ tot_emp_log_change_nat+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )
reg_13<-felm(main_mean ~ tot_emp_log_change_nat+Unemployment_Rate+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )

reg_14<-felm(main_ratio ~ tot_emp_log_change_nat | as.factor(year) | 0 |Employer, data=panel_main)
reg_15<-felm(main_ratio ~ tot_emp_log_change_nat+college+parttime+bon_com |as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+ as.factor(Sector)+IsSpecialized | 0 |Employer, data=panel_main )
reg_16<-felm(main_ratio ~ tot_emp_log_change_nat+college+parttime+bon_com+logSize+gprofit+mlev+tonbiq+roe | as.factor(BestFitMSA)+as.factor(year)+as.factor(OccFam)+IsSpecialized+as.factor(Employer) | 0 |Employer, data=panel_main )
reg_17<-felm(main_ratio ~ tot_emp_log_change_nat+college+parttime+bon_com+ | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )
reg_18<-felm(main_ratio ~ tot_emp_log_change_nat+Unemployment_Rate+college+parttime+bon_com | as.factor(BestFitMSA)+as.factor(OccFam)+IsSpecialized+as.factor(Employer):as.factor(year) | 0 |Employer, data=panel_main )


texreg(list(reg_9, reg_10, reg_11, reg_12, reg_13), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/emp_reg1.txt')
texreg(list( reg_14, reg_15, reg_16, reg_17, reg_18), digits =4, file='/global/home/pc_moseguera/data/Burning Glass 2/Regression Tables/emp_reg2.txt')


