# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 12:42:47 2020

@author: Liza Marie Soriano
"""

#import sys
#sys.path.insert(0, '../Data') #path to datasets
import pandas as pd

#####################
# PATH TO DATAFILES #
#####################

CRIMES_18 = "Crimes_-_2018"


#####################
# DATASET VARIABLES #
#####################

['ID', 'Case Number', 'Date', 'Block', 'IUCR', 'Primary Type',
       'Description', 'Location Description', 'Arrest', 'Domestic', 'Beat',
       'District', 'Ward', 'Community Area', 'FBI Code', 'X Coordinate',
       'Y Coordinate', 'Year', 'Updated On', 'Latitude', 'Longitude',
       'Location']


##################
# READ AND CLEAN #
##################

df = pd.read_csv(CRIMES_18)

''' CHECK '''
df.shape # (267,767, 22)
df['Primary Type'].nunique() # 32
df['Community Area'].nunique() # 78
df['Location'].count() # 263,420 non-null values
df['Location'].isna().sum() # correctly 4347 (missing)


''' MODIFY ATTRIBUTES '''
# Change Date type and add month & year columns
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
