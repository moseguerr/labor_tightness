# Load libraries
library(dplyr)
library(fredr)
library(lubridate)
library(estimatr)


### Load data
panel_main <- read_dta("/Volumes/TOSHIBA EXT/final_variables/panel_main.dta")
###  Keep only data that has merged with unemployment
panel_main <- panel_main[panel_main$`_merge` != 0, ]
### Sort data
panel_main <- panel_main %>% 
  arrange(BestFitMSA, year,quarter, employer)
### Divide Unemployment to Have Proportions
panel_main$Unemployment_Rate<-(panel_main$Unemployment_Rate)/100

###First simple regression per Hypothesis
###Hypothesis 1
formula <- as.formula("prosocial ~ Unemployment_Rate")
m1 <- lm_robust(formula = formula,
                      data = panel_main,
                      clusters=BestFitMSA,
                      se_type = "stata")

###Hypothesis 2
formula <- as.formula("prosocial ~ spe_skill_mean")
m2 <- lm_robust(formula = formula,
                             data = panel_main,
                             clusters=BestFitMSA,
                             se_type = "stata")
summary(model_h2_simple)

###Hypothesis 2b 
subselect<-panel_main %>% select(ends_with(c("mean")) & starts_with(c("occ")),-"occ_not_defined_mean")
xname<-colnames(subselect)
fmla<- as.formula(paste("prosocial ~ ", paste(xname, collapse= "+")))
m2b <- lm_robust(formula=fmla ,
                       data = panel_main, 
                       clusters=BestFitMSA,
                       se_type = "stata")

###Hypothesis 3
formula <- as.formula("prosocial ~ spe_skill_growth")
m3 <- lm_robust(formula = formula,
                             data = panel_main,
                             clusters=BestFitMSA,
                             se_type = "stata")


###Hypothesis 3b 
subselect<-panel_main %>% select(ends_with(c("mean")) & starts_with(c("occ")),-"occ_not_defined_mean")
xname<-colnames(subselect)
fmla <- as.formula(paste("prosocial ~ ", paste(xname, collapse= "+"),"+year"))
m3 <- lm_robust(formula=fmla ,
                              data = panel_main, 
                              clusters=BestFitMSA,
                              se_type = "stata")

###Hypothesis Together
formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth")
m4 <- lm_robust(formula = formula,
                             data = panel_main,
                             clusters=BestFitMSA,
                             se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)+factor(year)+gprofit")
m5 <- lm_robust(formula = formula,
                              data = panel_main,
                              clusters=BestFitMSA,
                              se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)+factor(year)")
m5b <- lm_robust(formula = formula,
                data = panel_main,
                clusters=BestFitMSA,
                se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)+factor(year)+factor(sector)+gprofit")
m6 <- lm_robust(formula = formula,
                data = panel_main,
                clusters=BestFitMSA,
                se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)+factor(year)+factor(sector)")
m6 <- lm_robust(formula = formula,
                data = panel_main,
                clusters=BestFitMSA,
                se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)+factor(year)+factor(employer)")
m7 <- lm_robust(formula = formula,
                data = panel_main,
                clusters=BestFitMSA,
                se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)")
m8 <- lm_robust(formula = formula,
                data = panel_main,
                fixed_effects=(year*sector),
                clusters=BestFitMSA,
                se_type = "stata")

formula <- as.formula("prosocial ~ Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)")
m9 <- lm_robust(formula = formula,
                data = panel_main,
                fixed_effects=(year*employer),
                clusters=BestFitMSA,
                se_type = "stata")

###Hypothesis 3b 
subselect<-panel_main %>% select(ends_with(c("mean")) & starts_with(c("occ")),-"occ_not_defined_mean")
xname<-colnames(subselect)
fmla <- as.formula(paste("prosocial ~ ", paste(xname, collapse= "+"),"+factor(year)+Unemployment_Rate+spe_skill_mean+spe_skill_growth+factor(ST_FIPS_Code)"))
m10 <- lm_robust(formula=fmla ,
                data = panel_main,
                fixed_effects = sector,
                clusters=BestFitMSA,
                se_type = "stata")


save(m1,m2,m3,m4,m5,m6,m7,m8,m9,m19,file = '/Users/glevinkonigsberg/Documents/MGOR/2yp/test.RData')

