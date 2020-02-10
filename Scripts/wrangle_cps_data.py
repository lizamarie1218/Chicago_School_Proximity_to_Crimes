# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 13:19:27 2020

@author: Liza Marie Soriano
"""

#import sys
#sys.path.insert(0, '../Data') #path to datasets
import pandas as pd
import util

#####################
# PATH TO DATAFILES #
#####################

CPS_RAW_1718 = "../Data/Chicago_Public_Schools_-_School_Profile_Information_SY1718.csv"
CPS_RAW_1819 = "../Data/Chicago_Public_Schools_-_School_Profile_Information_SY1819.csv"


#####################
# DATASET VARIABLES #
#####################

DEMOGRAPHICS = ['Student_Count_Total', 'Student_Count_Low_Income',
       'Student_Count_Special_Ed', 'Student_Count_English_Learners',
       'Student_Count_Black', 'Student_Count_Hispanic', 'Student_Count_White',
       'Student_Count_Asian', 'Student_Count_Native_American',
       'Student_Count_Other_Ethnicity', 'Student_Count_Asian_Pacific_Islander',
       'Student_Count_Multi', 'Student_Count_Hawaiian_Pacific_Islander',
       'Student_Count_Ethnicity_Not_Available', 'Statistics_Description',
       'Demographic_Description', 'Classroom_Languages',
       'Bilingual_Services', 'Refugee_Services', 'Title_1_Eligible',
       'Hard_Of_Hearing', 'Visual_Impairments']

LOCATION = ['Address', 'City', 'State', 'Zip', 'School_Latitude', 'School_Longitude']

TRANSPORTATION = ['Transportation_Bus', 'Transportation_El', 'Transportation_Metra']

OUTCOMES = ['Average_ACT_School', 'Mean_ACT',
       'College_Enrollment_Rate_School', 'College_Enrollment_Rate_Mean',
       'Graduation_Rate_School', 'Graduation_Rate_Mean', 'Overall_Rating',
       'Rating_Status', 'Rating_Statement', 'Classification_Description']

GRADES = ['Primary_Category', 'Is_High_School', 'Is_Middle_School',
       'Is_Elementary_School', 'Is_Pre_School']

['School_ID', 'Legacy_Unit_ID', 'Finance_ID', 'Short_Name', 'Long_Name', 'Summary',
       'Administrator_Title', 'Administrator', 'Secondary_Contact_Title',
       'Secondary_Contact', 'Phone', 'Fax',
       'CPS_School_Profile', 'Website', 'Facebook', 'Twitter', 'Youtube',
       'Pinterest', 'Attendance_Boundaries', 'Grades_Offered_All',
       'Grades_Offered', 'Dress_Code', 'PreK_School_Day',
       'Kindergarten_School_Day', 'School_Hours', 'Freshman_Start_End_Time',
       'After_School_Hours', 'Earliest_Drop_Off_Time',
       'PreSchool_Inclusive', 'Preschool_Instructional',
       'Significantly_Modified', 'School_Year', 'Third_Contact_Title', 'Third_Contact_Name',
       'Fourth_Contact_Title', 'Fourth_Contact_Name', 'Fifth_Contact_Title',
       'Fifth_Contact_Name', 'Sixth_Contact_Title', 'Sixth_Contact_Name',
       'Seventh_Contact_Title', 'Seventh_Contact_Name', 'Network',
       'Is_GoCPS_Participant', 'Is_GoCPS_PreK', 'Is_GoCPS_Elementary',
       'Is_GoCPS_High_School', 'Open_For_Enrollment_Date',
       'Closed_For_Enrollment_Date']


###########################
# READ AND CLEAN:         #
#   School Year 2018-2019 #
###########################
df = util.read_csv(CPS_RAW_1819, col_types={'School_ID':str})

''' CHECK '''
df.shape # 654x92
df['School_ID'].nunique()   # Look at uniqueness of School_ID
df['College_Enrollment_Rate_School'].count() # 166 non-null values
df['College_Enrollment_Rate_School'].isna().sum() # correctly 488 (missing)
df['Graduation_Rate_School'].isna().sum() # 512 of 654 missing
df['Mean_ACT'].isna().sum() # All 654 missing
df.Rating_Status.value_counts() # 125 with value "Not Applicable"


''' ADD ATTRIBUTES '''
def add_attributes(df, schoolyear):
    '''
    Add schoolyear and demographics info

    INPUTS: cps_df, schoolyear as YYYY-YYYY (str)
    '''
    # Add School Year
    df['schoolyear'] = schoolyear

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
        df[perc] = df[count] / df['Student_Count_Total']

    # Add Majority Race column
    df.loc[(df['%black'] > 0.5), 'majority_race'] = 'majority_black'
    df.loc[(df['%hisp'] > 0.5), 'majority_race'] = 'majority_hisp'
    df.loc[(df['%white'] > 0.5), 'majority_race'] = 'majority_white'
    df['majority_race'].fillna('no_majority', inplace = True)

    return df


new_cols = ['%low_inc', '%special_ed', '%esl', '%black', '%hisp', '%white', '%asian', \
            '%native', '%other', '%as.pacif', '%multirace', '%hw.pacif', '%na']

