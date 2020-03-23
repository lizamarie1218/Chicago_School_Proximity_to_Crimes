# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 19:07:23 2020

@author: Liza Marie Soriano
"""

import pandas as pd
import numpy as np

###################################################################################
# DATASET VARIABLES
###################################################################################
CPS_1617 = "../Data/Chicago_Public_Schools_-_School_Profile_Information_SY1617.csv"
CPS_COHORT = "../Data/5-Year_HS_Cohort_Rates.csv"
CPS_PERSIST = "../Data/College_Enrollment_Persistence_2010-2018.csv"


####################
# GLOBAL VARIABLES #
####################
# Define cols to upload and to change to numeric - GRADUATION/DROPOUT INFO
cohort_cols = ['School_ID',
               'School_Name',
               'Num_Dropout_5yr_2017', 
               'Num_Grad_5yr_2017', 
               'Num_Students_Adjusted_2017']

persist_cols = ['School_ID',
                'School_Name',
                'Graduates_2017',
                'Enrollments_2017', 'Enrollment_Pct_2017',
                'Num_Enrollments_Persisting_2017', 'Persistence_Pct_2017']

to_numeric = ['Num_Dropout_5yr_2017',
              'Num_Grad_5yr_2017',
              'Num_Students_Adjusted_2017',
              'Graduates_2017',
              'Enrollments_2017', 'Enrollment_Pct_2017',
              'Num_Enrollments_Persisting_2017', 'Persistence_Pct_2017']

#############################
# READ, MERGE, & CLEAN DATA #
#############################
''' CPS PROFILES '''
cps_df = pd.read_csv(CPS_1617, dtype={'School_ID':str}) #184 rows
cps_df = cps_df[cps_df['Is_High_School'] == 'Y'] # value is True after SY16-17


''' PERSISTENCE DATA '''
persist_df = pd.read_csv(CPS_PERSIST, usecols=persist_cols, dtype={'School_ID':str}) #177 rows

# Replace '*' entries in persistence columns
for col in persist_cols:
    persist_df[col] = persist_df[col].replace('*', np.nan)


''' COHORT DATA '''
cohort_df = pd.read_csv(CPS_COHORT, usecols=cohort_cols, dtype={'School_ID':str}) #169 rows

# Replace ' ' entries in cohort columns
for col in cohort_cols:
    cohort_df[col] = cohort_df[col].replace(' ', np.nan)


''' MERGE '''
grad_df = pd.merge(cps_df, persist_df, on="School_ID", how="left")
grad_df = pd.merge(grad_df, cohort_df, on="School_ID", how="left") #184 rows


''' CLEAN '''
# Change select columns to NUMERIC type
for col in to_numeric:
    grad_df[col] = pd.to_numeric(grad_df[col])


#######################
# IMPUTE OR DROP ROWS #
#######################

''' CHECK WHAT'S MISSING '''
#print(sum(grad_df['Long_Name'].isna())) #0 rows na
#print(sum(grad_df['School_Name_x'].isna())) #7 rows na (persist data)
#print(sum(grad_df['School_Name_y'].isna())) #48 rows na (cohort data)
#school_names = grad_df[['Long_Name', 'School_Name_x', 'School_Name_y']]
#for col in grad_df.columns:
#    print(col, ':', sum(grad_df[col].isna()))
'''
School_Name_x : 7
Graduates_2017 : 10
Enrollments_2017 : 10
Enrollment_Pct_2017 : 10
Num_Enrollments_Persisting_2017 : 26
Persistence_Pct_2017 : 26
School_Name_y : 48
Num_Dropout_5yr_2017 : 64
Num_Grad_5yr_2017 : 63
Num_Students_Adjusted_2017 : 61
'''

# Drop schools with missing data from both persist & cohort -- drops 10 rows
grad_df = grad_df[grad_df['Graduates_2017'].notna()] #Graduates_2017 col is a good proxy

# Use existing cohort graduation numbers to calculate graduation rates
grad_df['graduation_rates'] = grad_df.Num_Grad_5yr_2017 / grad_df.Num_Students_Adjusted_2017
#print(sum(grad_df['Num_Grad_5yr_2017'].isna())) #53
#print(sum(grad_df['graduation_rates'].isna())) #53

# Use existing cohort dropout numbers to calculate dropout rates
grad_df['dropout_rates'] = grad_df.Num_Dropout_5yr_2017 / grad_df.Num_Students_Adjusted_2017
#print(sum(grad_df['Num_Dropout_5yr_2017'].isna())) #54
#print(sum(grad_df['dropout_rates'].isna())) #54

# Add cols for imputation
impute_cols = ['graduation_rates', 'dropout_rates', 'Persistence_Pct_2017']
imputed = grad_df[impute_cols].isnull().astype(int).add_suffix('_imputed')
grad_df = pd.concat([grad_df, imputed], axis = 1)


''' IMPUTE GRADUATION COUNTS '''
# Use average graduation rates within groups of same zipcode and school ratings to impute
grad_df.graduation_rates.fillna(
        grad_df.groupby(['Zip', 'Rating_Status'])['graduation_rates'].transform('mean'), 
        inplace = True)
#print(sum(grad_df['graduation_rates'].isna())) #20

# Use average rates within groups of same school ratings to impute rest of NAs
grad_df.graduation_rates.fillna(
        grad_df.graduation_rates.groupby(grad_df.Rating_Status).transform('mean'), 
        inplace = True)
#print(sum(grad_df['graduation_rates'].isna())) #should be 0


''' IMPUTE DROPOUT COUNTS '''
# Use average dropout rates within groups of same zipcode and school ratings to impute
grad_df.dropout_rates.fillna(
        grad_df.groupby(['Zip', 'Rating_Status'])['dropout_rates'].transform('mean'), 
        inplace = True)
#print(sum(grad_df['dropout_rates'].isna())) #21

# Use average rates within groups of the same school ratings to impute rest of nas
grad_df.dropout_rates.fillna(
        grad_df.dropout_rates.groupby(grad_df.Rating_Status).transform('mean'), 
        inplace = True)
#print(sum(grad_df['dropout_rates'].isna())) #should be 0


''' IMPUTE PERSISTENCE COUNTS '''
# Use average dropout rates within groups of same zipcode and school ratings to impute
#print(sum(grad_df['Persistence_Pct_2017'].isna())) #16
grad_df.Persistence_Pct_2017.fillna(
        grad_df.groupby(['Zip', 'Rating_Status'])['Persistence_Pct_2017'].transform('mean'), 
        inplace = True)
#print(sum(grad_df['dropout_rates'].isna())) #6

# Use average rates within groups of the same school ratings to impute rest of nas
grad_df.Persistence_Pct_2017.fillna(
        grad_df.Persistence_Pct_2017.groupby(grad_df.Rating_Status).transform('mean'), 
        inplace = True)
#print(sum(grad_df['Persistence_Pct_2017'].isna())) #should be 0

''' CHECK '''
# Calculate other rate (not captured by graduation rate and dropout rate)
grad_df['other_rates'] = 1 - (grad_df.graduation_rates + grad_df.dropout_rates)

# Jones High School sums equal more than 1; school size doubled?
# Use average with CPS profile data grad_rate instead
grad_df.loc[grad_df['School_ID'] == '609678', 
            'graduation_rates'] = (grad_df.Graduation_Rate_School / 100 + \
            grad_df.graduation_rates) / 2
grad_df.loc[grad_df['School_ID'] == '609678',
            'dropout_rates'] = 1 - grad_df.graduation_rates

# Recalculate other rate
grad_df['other_rates'] = 1 - (grad_df.graduation_rates + grad_df.dropout_rates)



###################
# CALCULATE RATES #
###################

# Calculate college enrollment rate (cohort data grad rate * perst data enroll/grad)
grad_df['enrollment_rates'] =   grad_df.graduation_rates * grad_df.Enrollment_Pct_2017 / 100

# Calculate college persistence (enrollment rate * perst data perst/enrolled)
grad_df['persistence_rates'] =   grad_df.enrollment_rates * grad_df.Persistence_Pct_2017 / 100

# RE-calculate high school GRADUATED ONLY rate (grad only = grad - all enrolled)
grad_df['graduation_only'] = grad_df.graduation_rates - grad_df.enrollment_rates

# RE-calculate college ENROLLMENT ONLY rate (enrollment_only = all enrolled - persisted)
grad_df['enrollment_only'] = grad_df.enrollment_rates - grad_df.persistence_rates

# CHECK TOTAL
grad_df['check_total'] =    grad_df.dropout_rates + grad_df.graduation_only + \
                            grad_df.enrollment_only + grad_df.persistence_rates + \
                            grad_df.other_rates



################
# SAVE TO FILE #
################ 
grad_df.to_csv('../Data/CPS_OUTCOMES_2017.csv', index=False)




########################
# UNUSED/REPLACED CODE #
########################
#''' IMPUTE COUNTS '''
# Look at schools with missing class count/size data
#missing_df = grad_df[grad_df['Num_Students_Adjusted_2017'].isna()]

# Use CPS Profile's Student_Count_Total / # of Grades to estimate size of one cohort class
#grad_df['num_grades_offered'] = grad_df.apply(
#        lambda row: len(row.Grades_Offered_All.split(',')), axis=1)
#grad_df.Num_Students_Adjusted_2017.fillna(
#        round(grad_df.Student_Count_Total / grad_df['num_grades_offered']))

# Use 'Graduates_2017' column to fill missing 'Num_Grad_5yr_2017' rows
#grad_df.Num_Grad_5yr_2017.fillna(grad_df.Graduates_2017, inplace=True)

# Use mean dropout rates to calculate total students as an imputation 
#grad_df.Num_Students_Adjusted_2017.fillna(  round(grad_df.Num_Grad_5yr_2017 / 
#                                                (1 - grad_df['dropout_rates'].mean()) ),
#                                           inplace=True)
#print(sum(grad_df['Num_Students_Adjusted_2017'].isna())) #should be 0 now

#print(sum(grad_df['Num_Dropout_5yr_2017'].isna())) #54
# Use count difference to calculate dropouts as an imputation
#grad_df.Num_Dropout_5yr_2017.fillna(grad_df.Num_Students_Adjusted_2017 - 
#                                   grad_df.Num_Grad_5yr_2017, 
#                                inplace=True)
#print(sum(grad_df['Num_Dropout_5yr_2017'].isna())) #should be 0 now

# Use existing persistence numbers to calculate average persistence rate
#grad_df['persistence_rates'] = grad_df.Num_Enrollments_Persisting_2017 / grad_df.Enrollments_2017

# Use mean dropout rates to calculate total students as an imputation 
#grad_df.Num_Enrollments_Persisting_2017.fillna(  round(grad_df.persistence_rates.mean() *
#                                                grad_df.Enrollments_2017) , inplace=True)

#intensive_support = grad_df[grad_df['Rating_Status'] == 'Intensive Support']

# Use CPS profiles data to fill in some missing rates
#grad_df.graduation_rates.fillna(grad_df.Graduation_Rate_School / 100, inplace = True)
#grad_df.loc[grad_df.Overall_Rating != "Inability to Rate",'Graduation_Rate_School'].fillna(
#        grad_df.Graduation_Rate_School / 100, inplace = True)
#print(sum(grad_df['graduation_rates'].isna())) #48

# Calculate college ENROLLMENT ONLY rate (enrollment_only = enrolled - persisted)
#grad_df['enrollment_rates'] =   round(grad_df.Enrollments_2017 / \
#                                  grad_df.Num_Students_Adjusted_2017, 2) - \
#                               (grad_df.persistence_rates)


# Repopulate dropout rate previously calculated for imputation
#grad_df['dropout_rates'] = round(grad_df.dropout_rates, 2)

# Repopulate persistence rate previously calculated for imputation (diff definition now)
#grad_df['persistence_rates'] = None
#grad_df['persistence_rates'] =  round(grad_df.Num_Enrollments_Persisting_2017 / \
#                                grad_df.Num_Students_Adjusted_2017, 2)



# Calculate high school GRADUATION ONLY rate (grad only = grad - enrolled - persisted)
#grad_df['graduation_rates'] = None
#grad_df['graduation_rates'] = round(grad_df.Num_Grad_5yr_2017 / \
#                                   grad_df.Num_Students_Adjusted_2017, 2) - \
#                                (grad_df.enrollment_rates + grad_df.persistence_rates)

# Add up rate numbers (should be close to 1)
#grad_df['total_of_rates'] = round(grad_df.dropout_rates + grad_df.graduation_rates + \
#                        grad_df.enrollment_rates + grad_df.persistence_rates, 2)

# Add column for reamining share (non-graduates, transferred, lack of data, etc.)
#grad_df['other'] = round(1 - grad_df.total_of_rates, 2)