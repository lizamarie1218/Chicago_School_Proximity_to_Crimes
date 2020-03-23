# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 15:02:22 2020

@author: Liza Marie Soriano
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.geometry import Point

from wrangle_crime_data import read_crimes


####################
# GLOBAL VARIABLES #
####################
# Datasets
CPS_OUTCOMES = "../Data/CPS_OUTCOMES_2017.csv"
COMM_AREAS = "../Data/Boundaries - Community Areas (current).geojson"
CRIMES_15 = "../Data/Crimes_-_2015.csv"
CRIMES_16 = "../Data/Crimes_-_2016.csv"
CRIMES_17 = "../Data/Crimes_-_2017.csv"

# Columns
CPS_COLS = ['School_ID', 'Long_Name', 'School_Latitude', 'School_Longitude', 
                 'dropout_rates', 'graduation_only', 'enrollment_only', 
                 'persistence_rates', 'other_rates']

VIOLENT_CRIMES = ['BATTERY', 'ASSAULT', 'ROBBERY', 'HOMICIDE',
                  'CRIM SEXUAL ASSAULT',  'CRIMINAL SEXUAL ASSAULT', 'SEX OFFENSE']

PROPERTY_CRIMES = ['THEFT', 'CRIMINAL DAMAGE', 'BURGLARY', 'MOTOR VEHICLE THEFT', 'ARSON']

GUN_CRIMES = ['WEAPONS VIOLATION'] #or use IUCR codes that indicate gun/firearm use?

'''
THEFT                                123873
BATTERY                               99122
CRIMINAL DAMAGE                       60685
ASSAULT                               37258
DECEPTIVE PRACTICE                    37243
OTHER OFFENSE                         34931
NARCOTICS                             28623
BURGLARY                              28056
ROBBERY                               23264
MOTOR VEHICLE THEFT                   22259
CRIMINAL TRESPASS                     12911
WEAPONS VIOLATION                      7649
OFFENSE INVOLVING CHILDREN             4605*
PUBLIC PEACE VIOLATION                 3398
CRIM SEXUAL ASSAULT                    3130
INTERFERENCE WITH PUBLIC OFFICER       2093
SEX OFFENSE                            2022
PROSTITUTION                           1678
HOMICIDE                               1431
ARSON                                   991
LIQUOR LAW VIOLATION                    456
KIDNAPPING                              397*
GAMBLING                                392
STALKING                                365*
INTIMIDATION                            274
OBSCENITY                               113
CONCEALED CARRY LICENSE VIOLATION        90
NON-CRIMINAL                             82
PUBLIC INDECENCY                         22
HUMAN TRAFFICKING                        22*
CRIMINAL SEXUAL ASSAULT                  14
NON - CRIMINAL                           11
OTHER NARCOTIC VIOLATION                 10
NON-CRIMINAL (SUBJECT SPECIFIED)          3
'''


#######################################
# LOAD -- CPS and Community Area Data #
#######################################
''' CPS OUTCOMES '''
cps_df = pd.read_csv(CPS_OUTCOMES, dtype={'School_ID':str})
cps_df = cps_df[CPS_COLS]
cps_df['coordinates'] = list(zip(cps_df.School_Latitude, cps_df.School_Longitude))


''' COMMUNITY AREAS '''
# Load GeoJson of Community Area boundaries
comm_bounds = gpd.read_file(COMM_AREAS)

# Determine center of each polygon and add as columns
comm_bounds['centroid_lon'] = comm_bounds['geometry'].centroid.x
comm_bounds['centroid_lat'] = comm_bounds['geometry'].centroid.y


###########################################
# LOAD -- Crimes Data (09/2015 - 08/2017) #
###########################################
''' CRIMES DATA '''
crimes_15 = read_crimes(CRIMES_15) #264,343 x 23
crimes_16 = read_crimes(CRIMES_16) #269,327 x 23
crimes_17 = read_crimes(CRIMES_17) #268,535 x 23

# Filter for desired months
crimes_15 = crimes_15[crimes_15['Month'] >= 9] #87,858 x 23
crimes_17 = crimes_17[crimes_17['Month'] <= 8] #180,288 x 23

# Concatenate crimes together
crimes_df = pd.concat([crimes_15, crimes_16]) #357,185 x 23
crimes_df = pd.concat([crimes_df, crimes_17]) #537,473 x 23

# Shortcut
#crimes_df = pd.concat([crimes_15[crimes_15['Month'] >= 9], crimes_16])
#crimes_df = pd.concat([crimes_df, crimes_17[crimes_17['Month'] <= 8]])


''' MERGE '''
# Merge crimes data with area boundaries data
crimes_gdf = crimes_df.merge(comm_bounds,
                             left_on='Community Area',
                             right_on='area_num_1',
                             how='left') #537,473 x 35

''' IMPUTE LOCATIONS '''
def impute_locations(crimes_gdf):
    '''
    Fill NA locations with centroid of Community Area by which each crime belongs
    '''
    # Add columns indicating imputed rows
    imputed = crimes_gdf[['Longitude', 'Latitude']].isnull().astype(int).add_suffix('_imputed')
    crimes_gdf = pd.concat([crimes_gdf, imputed], axis = 1)

    # Since only 6827 missing locations out of 539K+, this is okay
    print('missing before:', sum(crimes_gdf.Location.isna())) #6827

    #crimes_gdf.Location.fillna(crimes_gdf.ca_center, inplace = True)
    crimes_gdf.Latitude.fillna(crimes_gdf.centroid_lat, inplace = True)
    crimes_gdf.Longitude.fillna(crimes_gdf.centroid_lon, inplace = True)

    # Did it this way because crimes_df had Locations in a str, so needed to change format too
    crimes_gdf['Location'] = list(zip(crimes_gdf.Latitude, crimes_gdf.Longitude))
    print('missing after:', sum(crimes_gdf.Location.isna())) #0

    return crimes_gdf

# Impute
crimes_gdf = impute_locations(crimes_gdf) #537,473 x 37


#####################################################
# FIND CPS SCHOOL VORONOIS WHERE EACH CRIME BELONGS #
#####################################################

# https://stackoverflow.com/questions/45883314/python-check-and-count-how-many-where-points-sit-within-voronoi-cells
#points = [[0,0], [1,4], [2,3], [4,1], [1,1], [2,2], [5,3]]
# Grab list of school seeds from which to find "voronoi"
cps_points = np.array(list(cps_df.coordinates))

# Create kdtree object that is like a voronoi
voronoi_kdtree = cKDTree(cps_points)

#extraPoints = [[0.5,0.2], [3, 0], [4,0],[5,0], [4,3]]
# Grab list of crime points for which to find the nearest school
crime_points = np.array(list(crimes_gdf.Location))

# Find distance to and the schools nearest to each crime
point_dist, point_regions = voronoi_kdtree.query(crime_points)

# Add column to crimes_gdf that assigns each crime to a CPS school
crimes_gdf['nearest_school'] = point_regions #537,473 x 38

# Merge CPS and crimes data
crimes_gdf = crimes_gdf.merge(cps_df[['School_ID', 'Long_Name']], 
                              right_index=True, left_on='nearest_school') #537,473 x 40


#######################################
# GET SUMMARY CRIME COUNTS PER SCHOOL #
#######################################

''' TOTAL CRIMES '''
# Get total crime counts per school voronoi and merge with school info
total_crimes = crimes_gdf.School_ID.value_counts().reset_index()
total_crimes.columns = ['School_ID', 'total_crimes']
school_crimes = pd.merge(cps_df, total_crimes, on='School_ID') #174 x 11


def count_crime_type(crimes_df, type_col, crime_type, groupby, count_col, new_col, school_df):
    counts = crimes_df[crimes_df[type_col].isin(crime_type)].groupby([groupby], as_index=False)[count_col].count()
    counts.columns = [groupby, new_col]
    school_df = pd.merge(school_df, counts, on=groupby)
    return school_df


''' VIOLENT CRIMES '''
school_crimes = count_crime_type(crimes_gdf, 'Offense Type',
                                 VIOLENT_CRIMES, 'School_ID',
                                 'IUCR', 'vc_count',
                                 school_crimes)
#crimes_gdf[crimes_gdf['Offense Type'].isin(VIOLENT_CRIMES)].groupby(['School_ID'], as_index=False).IUCR.count()
#vc = crimes_gdf[crimes_gdf['Offense Type'].isin(VIOLENT_CRIMES)]
#            .groupby(['School_ID'], as_index=False)
#            .IUCR #any colname needed just for counts
#            .count()
#vc.columns = ['School_ID', 'vc_count']
#school_crimes = pd.merge(school_crimes, vc, on='School_ID') #174 x 12


''' PROPERTY CRIMES '''
school_crimes = count_crime_type(crimes_gdf, 'Offense Type',
                                 PROPERTY_CRIMES, 'School_ID',
                                 'IUCR', 'pc_count',
                                 school_crimes)
#crimes_gdf[crimes_gdf['Offense Type'].isin(PROPERTY_CRIMES)].groupby(['School_ID'], as_index=False).IUCR.count()
#pc = crimes_gdf[crimes_gdf['Offense Type'].isin(PROPERTY_CRIMES)]
#            .groupby(['School_ID'], as_index=False)
#            .IUCR #any colname needed just for counts
#            .count()
#pc.columns = ['School_ID', 'pc_count']
#school_crimes = pd.merge(school_crimes, pc, on='School_ID') #174 x 13


''' GUN CRIMES '''
school_crimes = count_crime_type(crimes_gdf, 'Offense Type',
                                 GUN_CRIMES, 'School_ID',
                                 'IUCR', 'gc_count',
                                 school_crimes)


''' CRIME LEVELS '''

def crime_levels(df, base_col, new_col):
    label_col = new_col + '_label'
    number_col = new_col + '_number'

    df[label_col] = pd.qcut(df[base_col].rank(method='first'), 
             3, labels=["low", "medium", "high"])
    df[number_col] = pd.qcut(df[base_col].rank(method='first'), 
             3, labels=[1, 2, 3])
    return df


# All Crimes
school_crimes = crime_levels(school_crimes, 'total_crimes', 'allcrimes_level')  
#school_crimes['allcrimes_level_label'] = pd.qcut(school_crimes.total_crimes.rank(method='first'), 
#             3, labels=["low", "medium", "high"])
#school_crimes['allcrimes_level_number'] = pd.qcut(school_crimes.total_crimes.rank(method='first'), 
#             3, labels=[1, 2, 3])

# Violent Crimes
school_crimes = crime_levels(school_crimes, 'vc_count', 'vcrimes_level') 
#school_crimes['vcrimes_level_label'] = pd.qcut(school_crimes.vc_count.rank(method='first'), 
#             3, labels=["low", "medium", "high"])
#school_crimes['vcrimes_level_number'] = pd.qcut(school_crimes.vc_count.rank(method='first'), 
#             3, labels=[1, 2, 3])

# Property Crimes
school_crimes = crime_levels(school_crimes, 'pc_count', 'pcrimes_level')
#school_crimes['pcrimes_level_label'] = pd.qcut(school_crimes.pc_count.rank(method='first'), 
#             3, labels=["low", "medium", "high"])
#school_crimes['pcrimes_level_number'] = pd.qcut(school_crimes.pc_count.rank(method='first'), 
#             3, labels=[1, 2, 3])

# Gun Crimes
school_crimes = crime_levels(school_crimes, 'gc_count', 'gcrimes_level')

# Checks
#crimes_gdf.Long_Name.value_counts()
#sum(school_crimes.total_crimes) #should be 537,473
#crimes_gdf['Offense Type'].value_counts()
#sum(crimes_gdf['Offense Type'].value_counts()) #should be 537,473
#crimes_gdf.groupby(['Community Area', 'Long_Name']).ID.count()


################
# SAVE TO FILE #
################
# Create geodataframe from school_crimes
geometry = [Point(xy) for xy in zip(school_crimes.School_Longitude, school_crimes.School_Latitude)]
gdf = gpd.GeoDataFrame(school_crimes, geometry=geometry) #174 x 12

# Save to file
with open('../Data/SCHOOL_CRIMES.geojson', 'w') as file:
    file.write(gdf.to_json())
