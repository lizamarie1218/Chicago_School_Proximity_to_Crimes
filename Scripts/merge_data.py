# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 14:18:42 2020

@author: Liza Marie Soriano
"""

#import sys
#sys.path.insert(0, '../Data')

import pandas as pd
import numpy as np
#import json
#import altair as alt
#from altair.expr import datum, if_
#alt.renderers.enable('colab')

#!pip install geopandas
#import geopandas as gpd


#####################
# DATASET VARIABLES #
#####################
CPS_1718 = "Chicago_Public_Schools_-_School_Profile_Information_SY1718.csv"
CPS_1819 = "Chicago_Public_Schools_-_School_Profile_Information_SY1819.csv"
CPS_5yrGrad = "5-Year_HS_Cohort_Rates.csv"
CPS_4yrGrad = "4-Year_HS_Cohort_Rates.csv"
CPS_College = "College_Enrollment_Persistence_2010-2018.csv"

CRIMES_18 = "Crimes_-_2018.csv"
COMM_AREAS = "Boundaries - Community Areas (current).geojson"


####################
# GLOBAL VARIABLES #
####################
# Define cols to upload and to change to numeric - GRADUATION/DROPOUT INFO
grad_cohort_1516 = ['School_ID', 'Rate_Dropout_4yr_2019', 'Rate_Grad_4yr_2019']
grad_cohort_1415 = ['School_ID', 'Rate_Dropout_5yr_2019', 'Rate_Grad_5yr_2019']
grad_cols_numeric = ['Rate_Dropout_4yr_2019', 'Rate_Dropout_5yr_2019', 
                     'Rate_Grad_4yr_2019', 'Rate_Grad_5yr_2019']

####################
# HELPER FUNCTIONS #
####################

def read_csv(filename, cols=None, col_types=None):
  '''
  Inputs:
    name of file (str)--must end in .csv
    columns to include from original (list)--if not specified, read all cols
    specifications of datatypes of cols (dict of {col : dtype})
  Outputs:
  '''
  df = pd.read_csv(filename, usecols=cols, dtype=col_types)
  return df


def change_to_numeric(df, col_list):
    '''
    Change select columns to numeric datatype
    INPUTS: df, col_list (list of str) of attributes to change
    '''
    # Change select columns to NUMERIC type
    for col in col_list:
        df[col] = pd.to_numeric(df[col])


def remove_trailing_character(df, col_list, character=None):
    '''
    Remove character or trailing whitespace from values in df columns.
    INPUT: df | col_list (list of str) of colnames from which to remove character/whitespace | char (str) to remove
    OUTPUT: df edited in place
    '''
    if character:
      for col in col_list:
        df[col] = df[col].str.rstrip(character)
    else:
      for col in col_list:
        df[col] = df[col].str.rstrip()


#########################
# EXPLORE & MODIFY DATA #
#########################

def explore_cps_df(cps_data=CPS_1819):
    df = read_csv(cps_data, col_types={'School_ID':str})

    ''' CHECK '''
    df.shape # 654x92
    df['School_ID'].nunique()   # Look at uniqueness of School_ID
    df['College_Enrollment_Rate_School'].count() # 166 non-null values
    df['College_Enrollment_Rate_School'].isna().sum() # correctly 488 (missing)
    df['Graduation_Rate_School'].isna().sum() # 512 of 654 missing
    df['Mean_ACT'].isna().sum() # All 654 missing
    df.Rating_Status.value_counts() # 125 with value "Not Applicable"


def add_attributes_cps(cps_df, schoolyear):
    '''
    Add schoolyear and demographics info

    INPUTS: cps_df, schoolyear as 'YYYY-YYYY' (str)
    '''

    # Add School Year
    cps_df['schoolyear'] = schoolyear

    # Add % Demographics
    dmg_perc_cols = {'Student_Count_Low_Income': '%low_inc', \
                     'Student_Count_Special_Ed': '%special_ed', \
                     'Student_Count_English_Learners': '%esl', \
                     'Student_Count_Black': '%black', \
                     'Student_Count_Hispanic': '%hisp', \
                     'Student_Count_White': '%white', \
                     'Student_Count_Asian': '%asian', \
                     'Student_Count_Native_American': '%native', \
                     'Student_Count_Other_Ethnicity': '%other', \
                     'Student_Count_Asian_Pacific_Islander': '%as.pacif', \
                     'Student_Count_Multi': '%multirace', \
                     'Student_Count_Hawaiian_Pacific_Islander': '%hw.pacif', \
                     'Student_Count_Ethnicity_Not_Available': '%na'}

    for count, perc in dmg_perc_cols.items():
        cps_df[perc] = cps_df[count] / cps_df['Student_Count_Total']

    # Add Majority Race column
    cps_df.loc[(cps_df['%black'] > 0.5), 'majority_race'] = 'majority_black'
    cps_df.loc[(cps_df['%hisp'] > 0.5), 'majority_race'] = 'majority_hisp'
    cps_df.loc[(cps_df['%white'] > 0.5), 'majority_race'] = 'majority_white'
    cps_df['majority_race'].fillna('no_majority', inplace = True)
    
    return cps_df

def clean_data_grad(grad_df):
    ''' CLEAN UP DATA '''
    # Strip out '%' from the object values of rates
    remove_trailing_character(grad_df, grad_cols_numeric, '%')
    
    # Replace blank entries with NaNs (from: https://stackoverflow.com/questions/13445241/replacing-blank-values-white-space-with-nan-in-pandas)
    grad_df = grad_df.replace(r'^\s*$', np.nan, regex=True)
    
    # Convert cols to numeric
    change_to_numeric(grad_df, grad_cols_numeric)
    
    # Change cols to percentages
    for col in grad_cols_numeric:
      grad_df[col] = grad_df[col] / 100

    return grad_df


#############
# RUN MERGE #
#############
'''## READ IN DATASETS & MERGE ##'''
# Read in data & clean - CPS SCHOOLS
cps_df = read_csv("../Data/" + CPS_1819, col_types={'School_ID':str})
cps_df = add_attributes_cps(cps_df, '2018-2019')
cps_df = cps_df[cps_df['Is_High_School'] == True]

# Read in data & clean - GRADUATION/DROPOUT INFO
grad_df_4yr = read_csv("../Data/" + CPS_4yrGrad, cols=grad_cohort_1516, col_types={'School_ID':str})
grad_df_5yr = read_csv("../Data/" + CPS_5yrGrad, cols=grad_cohort_1415, col_types={'School_ID':str})
grad_df = pd.merge(grad_df_4yr, grad_df_5yr, on="School_ID", how='outer')
grad_df = clean_data_grad(grad_df)

# Merge CPS Profile Info with High School Graduation Outcomes Data
cps_df = pd.merge(cps_df, grad_df, on="School_ID", how='left')


##################
# TRANSFORM DATA #
##################
'''## CREATE MEANS FOR HS COHORTS ##'''
# Mean Graduation Percentage of High Schools
grad_mean_5yr_2019 = cps_df.loc[cps_df['Primary_Category'] == 'HS', 'Rate_Grad_5yr_2019'].mean()
grad_mean_4yr_2019 = cps_df.loc[cps_df['Primary_Category'] == 'HS', 'Rate_Grad_4yr_2019'].mean()

# Mean Dropout Percentage of High Schools
dropout_mean_5yr_2019 = cps_df.loc[cps_df['Primary_Category'] == 'HS', 'Rate_Dropout_5yr_2019'].mean()
dropout_mean_4yr_2019 = cps_df.loc[cps_df['Primary_Category'] == 'HS', 'Rate_Dropout_4yr_2019'].mean()


'''## CREATE CITYWIDE MEANS DATAFRAME ##'''
city_aggs = {'schoolyear_ending': [2019, 2019, 2019, 2019, 2019, 2019],
         'group': ['4-yr_cohort', '4-yr_cohort', '4-yr_cohort', '5-yr_cohort', '5-yr_cohort', '5-yr_cohort'],
         'rate_description': ['grad_rate', 'dropout_rate', 'other_rate', 'grad_rate', 'dropout_rate', 'other_rate'],
         'city_mean': [grad_mean_4yr_2019, dropout_mean_4yr_2019, 1-(grad_mean_4yr_2019 + dropout_mean_4yr_2019),
                       grad_mean_5yr_2019, dropout_mean_5yr_2019, 1-(grad_mean_5yr_2019 + dropout_mean_5yr_2019)]}
aggs_df = pd.DataFrame(data=city_aggs, dtype=np.int32)
aggs_df

'''## ADD COHORTS TO MEANS DATAFRAME ##'''
# Add Majority-Race Outcomes to aggregate df
# (4YR COHORT)
cohort_4yr = {'majority_black': 'majority_black_HS_4yr_cohort',
              'majority_hisp': 'majority_hisp_HS_4yr_cohort',
              'no_majority': 'no_majority_HS_4yr_cohort'}

for race, group in cohort_4yr.items():
  grad_mean = cps_df[cps_df['majority_race'] == race]['Rate_Grad_4yr_2019'].mean()
  dropout_mean = cps_df[cps_df['majority_race'] == race]['Rate_Dropout_4yr_2019'].mean()

  df = pd.DataFrame({"schoolyear_ending":[2019, 2019, 2019], 
                    "group":3*[group],
                    "rate_description":['grad_rate', 'dropout_rate', 'other_rate'],
                    "city_mean": [grad_mean, dropout_mean, (1-(grad_mean + dropout_mean))]
                     })
  aggs_df = aggs_df.append(df, ignore_index = True)

# Add Majority-Race Outcomes to aggregate df
# (5YR COHORT)
cohort_5yr = {'majority_black': 'majority_black_HS_5yr_cohort',
              'majority_hisp': 'majority_hisp_HS_5yr_cohort',
              'no_majority': 'no_majority_HS_5yr_cohort'}

for race, group in cohort_5yr.items():
  grad_mean = cps_df[cps_df['majority_race'] == race]['Rate_Grad_5yr_2019'].mean()
  dropout_mean = cps_df[cps_df['majority_race'] == race]['Rate_Dropout_5yr_2019'].mean()

  df = pd.DataFrame({"schoolyear_ending":[2019, 2019, 2019], 
                    "group":3*[group],
                    "rate_description":['grad_rate', 'dropout_rate', 'other_rate'],
                    "city_mean": [grad_mean, dropout_mean, (1-(grad_mean + dropout_mean))]
                     })
  aggs_df = aggs_df.append(df, ignore_index = True)


####################
# SAVE dfs TO FILE #
####################
# Save to csv
cps_df.to_csv('../Data/CPS_RATES.csv', index=False)
aggs_df.to_csv('../Data/CPS_RATES_MEANS.csv', index=False)