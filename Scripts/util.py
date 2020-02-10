# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 11:05:45 2020

@author: Liza Marie Soriano
"""

#import sys
import pandas as pd
#import numpy as np
#import json
import altair as alt
from altair.expr import datum, if_

#!pip install geopandas
import geopandas as gpd

###############################
# HELPER FUNCTIONS - CLEANING #
###############################

# FOR COLAB ONLY
def path_to_data(file):
    return '/content/drive/My Drive/Courses/CAPP 30239 - Data Viz for Policy Analysis/Data/{}'.format(file)


# FOR COLAB ONLY
def read_csv(filename, cols=None, col_types=None):
    '''
    Inputs:
        name of file (str)--must end in .csv
        columns to include from original (list)--if not specified, read all cols
        specifications of datatypes of cols (dict of {col : dtype})
    Outputs:
    '''
    df = pd.read_csv(path_to_data(filename), usecols=cols, dtype=col_types)
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


####################################
# HELPER FUNCTIONS - GEODATAFRAMES #
####################################

# Convert GeoPandas df back to GeoJson
def gen_geojson(geodataframe):
    ''' Converts GeoPandas dataframe back to GeoJson file that Altair can use for maps'''
    #choro_json = json.loads(crimes_gdf.to_json())
    #choro_data = alt.Data(values=choro_json['features'])
    data  = alt.InlineData(values = geodataframe.to_json(),
                          format = alt.DataFormat(property='features',
                                                  type='json'))
    return data


# Generate map
def gen_map(geodata, color_column, title):
    '''Generates map with crime choropleth and community area labels'''
    # Add Base Layer
    base = alt.Chart(geodata, title = title).mark_geoshape(
        stroke='black',
        strokeWidth=1
    ).encode(
    ).properties(
        width=400,
        height=400
    )
    # Add Choropleth Layer
    choro = alt.Chart(geodata).mark_geoshape(
        stroke='black'
    ).encode(
        color=alt.Color(color_column, 
                  type='quantitative', 
                  #scale=alt.Scale(scheme='bluegreen'),
                  title = "Crime Count")
    )
    # Add Labels Layer
    labels = alt.Chart(geodata).mark_text(baseline='top'
     ).properties(
        width=400,
        height=400
     ).encode(
         longitude='properties.centroid_lon:Q',
         latitude='properties.centroid_lat:Q',
         text='properties.community_area:O',
         size=alt.value(8),
         opacity=alt.value(1)
     )

    return base + choro + labels

