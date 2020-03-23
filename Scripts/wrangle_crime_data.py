# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 12:42:47 2020

@author: Liza Marie Soriano
"""

#import sys
#sys.path.insert(0, '../Data') #path to datasets
import pandas as pd
import geopandas as gpd

#####################
# PATH TO DATAFILES #
#####################

CRIMES_15 = "../Data/Crimes_-_2016.csv"
CRIMES_16 = "../Data/Crimes_-_2016.csv"
CRIMES_17 = "../Data/Crimes_-_2017.csv"
CRIMES_18 = "../Data/Crimes_-_2018.csv"
COMM_AREAS = "../Data/Boundaries - Community Areas (current).geojson"


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
def read_crimes(filepath):
    df = pd.read_csv(filepath, 
                     dtype={'ID':str, 
                            'Community Area':str, 
                            'Beat':str, 
                            'District':str, 
                            'Ward':str})

    # Change Date type and add month & year columns
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Rename column
    df.rename(columns = {'Primary Type':'Offense Type'}, inplace = True)

    return df


def check_crimes_df(df):
    # Explore
    print('SHAPE:', df.shape)
    print('COLUMNS:', df.columns)
    print('DATATYPES:', df.dtypes)
    print('UNIQUE VALUES - Offense Types:', df['Offense Type'].nunique())
    print('UNIQUE VALUES - Community Areas:', df['Community Area'].nunique())
    print('KNOWN CRIME LOCATIONS:', df['Location'].count())
    print('MISSING CRIME LOCATIONS:', df['Location'].isna().sum())


'''______EXAMPLE USE______ '''
#df = read_crimes(CRIMES_18)
#check_crimes_df(df)

# NUMBERS FOR CRIMES_18
    #df.shape # (267,767, 22)
    #df['Offense Type'].nunique() # 32
    #df['Community Area'].nunique() # 78
    #df['Location'].count() # 263,420 non-null values
    #df['Location'].isna().sum() # correctly 4347 (missing)


###########################
# GROUP BY COMMUNITY AREA #
###########################
''' Produces hood_crime_type df and hood_crimes df '''

def get_hood_crime_types(crimes_df):
    # Get a df counting crimes by Type within each Community Area
    hood_crime_type = crimes_df.groupby(['Community Area','Offense Type'], as_index=False)[['Date']].count()
    
    # Rename groupby/mini-df columns
    hood_crime_type.rename(columns = {'Community Area':'community_area', 
                                      'Date':'crime_count', 
                                      'Offense Type': 'offense_type'}, inplace = True)
    return hood_crime_type


'''______EXAMPLE USE______ '''
# Get hood_crime_type df
#hood_crime_type = get_hood_crime_types(df)

# Preview
#hood_crime_type.head()

# How many neighborhoods each crime type is seen
#hood_crime_type['offense_type'].value_counts().head()



def get_hood_crimes(hood_crime_type_df):
    # Get a df counting total crimes within each Community Area
    hood_crimes = hood_crime_type_df.groupby(['community_area'], as_index=False)[['crime_count']].sum()

    # Sort by crime_count
    hood_crimes = hood_crimes.sort_values(by=['crime_count'])
    
    return hood_crimes


'''______EXAMPLE USE______ '''
# Get hood_crimes df
#hood_crimes = get_hood_crimes(hood_crime_type)

# Preview
#hood_crimes

# Explore / Check Stats
# There are 2 crimes with NULL values for community area
#print('SHAPE:', hood_crimes.shape)
#print('TOTAL # OF CRIMES:', hood_crimes['crime_count'].sum())
#print('MISSING VALUES FOR COMM_AREA:', df['Community Area'].isna().sum())
#print('HIGHEST # OF CRIMES IN ONE COMM_AREA:', hood_crimes['crime_count'].max())


############################
# MERGE WITH CA BOUNDARIES #
############################

def merge_hood_ca_bounds(filepath, hood_crimes_df):
    # Load GeoJson of Community Area boundaries
    comm_bounds = gpd.read_file(filepath) #filepath ex: COMM_AREAS

    # Check that dataframe type is indeed geodataframe
    #print('DATAFRAME TYPE:', type(comm_bounds))
    #comm_bounds.head()

    # Merge crimes data with area boundaries data
    crimes_gdf = comm_bounds.merge(hood_crimes_df, 
                                   left_on='area_num_1', 
                                   right_on='community_area', 
                                   how='inner')

    # Check that dataframe type is still geodataframe & shape makes sense
    #print('DATAFRAME TYPE:', type(crimes_gdf))
    #print('DATFRAME SHAPE:', crimes_gdf.shape)
    #crimes_gdf.head()

    # Determine center of each polygon and add as columns
    crimes_gdf['centroid_lon'] = crimes_gdf['geometry'].centroid.x
    crimes_gdf['centroid_lat'] = crimes_gdf['geometry'].centroid.y
    #crimes_gdf.head()

    return crimes_gdf


####################################
# GET CRIME DATA FOR CLASS OF 2017 #
####################################
''' 
We want September 2015 – August 2017 crime data, which represents junior year until
summer after graduation for Class of 2017:

df_15 = read_crimes(CRIMES_15)
df_16 = read_crimes(CRIMES_16)
df_17 = read_crimes(CRIMES_17)

# Filter for desired months
df_15 = df_15[df_15['Month'] >= 9]
df_17 = df_17[df_17['Month'] <= 8]

'''
