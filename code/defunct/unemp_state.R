df_aux <- read_dta('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main.dta')
df_unem <- read_dta('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/unem_state_comp.dta')

df_aux <- df_aux %>%
  filter(df_aux$`_merge` != 0) %>% 
  select(-`_merge`)

df_unem1 <- df_unem %>% 
  rename(unem_ST = unemployment_rate) %>% 
  select(-c(index,ST,name_bgt,employer,gvkey))

df_aux <- df_aux %>% 
  left_join(by = c('year', 'quarter', 'ST_FIPS_Code'))

df_unem <- df_unem %>% 
  rename(unem_head = unemployment_rate, ST_head = ST_FIPS_Code) %>% 
  select(-c('ST','gvkey','name_bgt','index'))

df_aux <- df_aux %>% 
  left_join(df_unem, by = c('year','quarter','employer'))

df_aux %>% write_dta('/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/merge_main/panel_main_ST.dta')