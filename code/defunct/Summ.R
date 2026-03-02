# Simular datos
library(dplyr)
library(tidyr)

### Load data
panel_main <- read_dta("/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main.dta")
###  Keep only data that has merged with unemployment
panel_main <- panel_main[panel_main$`_merge` != 0, ]
### Sort data
panel_main <- panel_main %>%
  arrange(BestFitMSA, year,quarter, employer)
### Divide Unemployment to Have Proportions
panel_main$Unemployment_Rate<-(panel_main$Unemployment_Rate)/100

df <- panel_main %>% 
  select(prosocial,Unemployment_Rate,spe_skill_mean, gprofit,logSize,mlev,tonbiq, roe) # quedarse sólo con variables de interes


df <- df %>%
  pivot_longer(c(prosocial,Unemployment_Rate,spe_skill_mean, gprofit,logSize,mlev,tonbiq, roe),names_to = 'variables', values_to = "value") %>%
  arrange(variables) # reformatear la tabla

dfSum <- df %>% 
  group_by(variables) %>% 
  summarise(mean = mean(value, na.rm = T),
            sd = sd(value, na.rm = T),
            min = min(value, na.rm = T),
            max = max(value, na.rm = T),
            median = quantile(value, probs = 0.5, na.rm = T))

write.csv(dfSum,"/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/summarize.csv")
