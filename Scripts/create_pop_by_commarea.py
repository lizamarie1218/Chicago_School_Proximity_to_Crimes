# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 10:36:44 2020

@author: Liza Marie Soriano
"""

import pandas as pd
import sys

#####################
# PATH TO DATAFILES #
#####################

''' Path to data from Scripts/ directory '''
TRACT_TO_COMM = "../Data/2010 Tract to Community Area Equivalency File.csv"

TRACT_POP_2018 = "../Data/Chicago_Tracts_Pop_2018.json"
COMM_POP_2018 = "../Data/Chicago_CommAreas_Pop_2018.csv"


################################
# READ & CLEAN POPULATION DATA #
################################
def read_tracts_pop(filepath):
    '''
    Reads in json file saved from ACS. 
    Assumes population (B01003_001E), state, county, tract columns.

    Input: path to json file
    Output: df
    '''
    tract_pop = pd.read_json(filepath)
    # Grab column names from first row and use to rename df cols
    colnames = list(tract_pop.loc[0])
    tract_pop = tract_pop.rename(columns={0: "population", 
                                  1: colnames[1],
                                  2: colnames[2],
                                  3: colnames[3]})
    # Take out first row
    tract_pop = tract_pop.loc[1:]

    # Reset index so that it starts at 0 again (and without adding an index column)
    tract_pop = tract_pop.reset_index(drop=True)
    
    # Change population to numeric dtype
    tract_pop = tract_pop.astype({'population': 'int32'})

    return tract_pop


####################
# RUN FROM IPYTHON #
####################
def run(filepath):
    '''
    Runs all functions and returns df of population by community area.

    INPUTS: filepath to json (str), e.g. '../Data/file.json'
    OUTPUTS: csv file
    '''
    tract_pop = read_tracts_pop(filepath)

    # read and clean tract-community area data
    tract_comm = pd.read_csv(TRACT_TO_COMM)
    tract_comm = tract_comm[['CHGOCA', 'TRACT', 'GEOID2']].sort_values('CHGOCA', ascending = 1)
    tract_comm = tract_comm.reset_index(drop=True)
    tract_comm = tract_comm.astype({'CHGOCA': 'str', 'TRACT': 'str'})
        
    # Fill in leading 0s for tractS with less than 6 digits
    tract_comm['tract'] = tract_comm['TRACT'].astype(str).str.rjust(6,'0')

    # merge and group by community area
    ca_pop = tract_pop.merge(tract_comm, on='tract', how='right')
    ca_pop = ca_pop.groupby(['CHGOCA'], as_index= False)[['population']].sum()

    return ca_pop


#########################
# RUN FROM COMMAND LINE #
#########################
def go():
    '''
    Call script from command line
    '''
    usage = "Usage: python create_pop_by_commarea.py <json filepath> <csv directory>\n" \
            "<filepath> is path to json file of ACS data containing population by tract.\n" \
            "<csv directory> is path to save output csv. \n" \
            "Example: python create_pop_by_commarea.py '../Data/file.json' '../Data/file.csv' \n"

    num_args = len(sys.argv)
    args = sys.argv

    if num_args != 3:
        print(usage)
        sys.exit(1)
    else:
        df = run(args[1]) #should be like TRACT_POP_2018
        df.to_csv(args[2]) #should be like COMM_POP_2018; WILL OVERWRITE ALREADY EXISTING FILES


if __name__ == "__main__":
    go()