# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 10:23:49 2020

@author: Liza Marie Soriano
"""

import pandas as pd
import geopandas as gpd
from geopandas.geoseries import *

import util
import wrangle_cps_data as cps


#####################
# PATH TO DATAFILES #
#####################

CPS_RAW_1718 = "../Data/Chicago_Public_Schools_-_School_Profile_Information_SY1718.csv"
CPS_RAW_1819 = "../Data/Chicago_Public_Schools_-_School_Profile_Information_SY1819.csv"
COMM_AREAS = "../Data/Boundaries - Community Areas (current)"

#############
# LOAD DATA #
#############

''' Load dataframe of CPS Profiles '''
cps_df = pd.read_csv(CPS_RAW_1819, dtype={'School_ID':str})
cps_df = cps.add_attributes(cps_df, '2018-2019')

''' Load GeoJson of Community Area boundaries '''
comm_bounds = gpd.read_file(COMM_AREAS + '.geojson')










''' Merge crimes data with area boundaries data '''
crimes_gdf = comm_bounds.merge(cps_df, left_on='area_num_1', right_on='community_area', how='inner')