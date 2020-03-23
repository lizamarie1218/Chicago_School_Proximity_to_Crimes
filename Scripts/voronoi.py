# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 14:03:07 2020

@author: Liza Marie Soriano
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import geoplot


###################################################################################
# DATASET VARIABLES
###################################################################################
cps_df = pd.read_csv("../Data/CPS_OUTCOMES_2017.csv" , dtype={'School_ID':str})
cps_df = cps_df[['School_ID', 'Long_Name', 'School_Latitude', 'School_Longitude', 
                 'dropout_rates', 'graduation_only', 'enrollment_only', 
                 'persistence_rates', 'other_rates']]
cps_df['coordinates'] = list(zip(cps_df.School_Latitude, cps_df.School_Longitude))

# Import Chicago data for region clipping
chicago = gpd.read_file('../Data/Boundaries - City.geojson')



###############################################################################
# FIND VORONOIS (create a geodataframe)
###############################################################################
#from: jeffmylife
#https://www.daniweb.com/programming/computer-science/tutorials/520314/how-to-make-quality-voronoi-diagrams
#https://github.com/jeffmylife/casual/blob/master/Voromap.ipynb
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt


def simple_voronoi(vor, saveas=None, lim=None):
    # Make Voronoi Diagram 
    fig = voronoi_plot_2d(vor, show_points=True, show_vertices=True, s=4)
    # Configure figure 
    fig.set_size_inches(5,5)
    plt.axis("equal")
    if lim:
        plt.xlim(*lim)
        plt.ylim(*lim)
        
    if not saveas is None:
        plt.savefig("../pics/%s.png"%saveas)
    plt.show()


def calc_polygons(df):
    vor = Voronoi(df[["School_Longitude",
                      "School_Latitude"]].values)
    regions, vertices = voronoi_finite_polygons_2d(vor)
    polygons = []
    for reg in regions:
        polygon = vertices[reg]
        polygons.append(polygon)
    return polygons


#TAKEN FROM: https://gist.github.com/pv/8036995
def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite
    regions.
    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.
    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.
    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()*2

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1] # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


# Calculate Voronoi Polygons
#points = np.array(list(cps_df.coordinates))
#vor = Voronoi(points)
#simple_voronoi(vor, lim=(-0.25,1.25))
cps_df["polygons"] = calc_polygons(cps_df)


#https://automating-gis-processes.github.io/2016/Lesson2-geopandas-basics.html
#creating-geometries-into-a-geodataframe

# Create geodataframe
vor_gdf = gpd.GeoDataFrame()
vor_gdf[['School_ID', 'Long_Name']] = cps_df[['School_ID', 'Long_Name']]

# Create Polygon objects from array coordinates
from shapely import geometry
polygons = []
# polygon takes list of lists of lon-lat pairs
polygons = [geometry.Polygon(row) for row in cps_df.polygons]
vor_gdf['geometry'] = polygons

# coordinate system / projection?
from fiona.crs import from_epsg
vor_gdf.crs = from_epsg(4326)

# save to file (shp or geojson)
vor_gdf.to_file(r"../Data/voronois.shp")
with open('../Data/voronois.geojson', 'w') as f:
    f.write(vor_gdf.to_json())

# Plot?
# TO DO: doesn't plot correctly; doesn't look right
#vor_gdf.plot()
geoplot.polyplot(vor_gdf, extent = chicago.total_bounds)
#geoplot.polyplot(voronois)
#geoplot.polyplot(voronois, extent=chicago)
#geoplot.polyplot(voronois, extent=chicago.total_bounds)


###############################################################################
# FIND VORONOIS (plots a map)
###############################################################################
# from:
#https://wellsr.com/python/python-voronoi-diagram-with-geopandas-and-geoplot/
def display_map1(gdf, clip, proj):
    # Setup the Voronoi axes; this creates the Voronoi regions
    ax = geoplot.voronoi(gdf,  # Define the GeoPandas DataFrame
                         #hue='values',  # df column used to color regions
                         clip = clip,  # Define the voronoi clipping (map edge)
                         projection = proj,  # Define the Projection
                         #cmap = 'Reds',  # color set
                         #k = None,  # No. of discretized buckets to create
                         #legend = True, # Create a legend
                         #edgecolor = 'white',  # Color of the voronoi boundaries
                         #linewidth = 0.01  # width of the voronoi boundary lines
                        )
    
    # Render the plot with a base map
    geoplot.polyplot(chicago,  # Base Map
                     ax = ax,  # Axis attribute we created above
                     extent = chicago.total_bounds,  # Set plotting boundaries to base map boundaries
                     edgecolor='black',  # Color of base map's edges
                     linewidth=1,  # Width of base map's edge lines
                     zorder=1  # Plot base map edges above the voronoi regions
                     )


def display_map2(gdf, clip, proj):
    # Setup the Voronoi axes; this creates the Voronoi regions
    ax = geoplot.voronoi(gdf,  # Define the GeoPandas DataFrame
                         hue='total_crimes',  # df column used to color regions
                         clip = clip,  # Define the voronoi clipping (map edge)
                         projection = proj,  # Define the Projection
                         legend = True, # Create a legend
                         edgecolor = 'white',  # Color of the voronoi boundaries
                        )
    
    # Render the plot with a base map
    geoplot.polyplot(chicago,  # Base Map
                     ax = ax,  # Axis attribute we created above
                     extent = chicago.total_bounds,  # Set plotting boundaries to base map boundaries
                     edgecolor='black',  # Color of base map's edges
                     linewidth=1,  # Width of base map's edge lines
                     zorder=1  # Plot base map edges above the voronoi regions
                     )
    

def display_map3(gdf, clip, proj):
    # Setup the Voronoi axes; this creates the Voronoi regions
    ax = geoplot.voronoi(gdf,  # Define the GeoPandas DataFrame
                         hue='total_crimes',  # df column used to color regions
                         clip = clip,  # Define the voronoi clipping (map edge)
                         projection = proj,  # Define the Projection
                         legend = True, # Create a legend
                         edgecolor = 'white',  # Color of the voronoi boundaries
                        )
    
    # Render the plot with a base map
    geoplot.choropleth(chicago,  # Base Map
                     ax = ax,  # Axis attribute we created above
                     extent = chicago.total_bounds,  # Set plotting boundaries to base map boundaries
                     edgecolor='black',  # Color of base map's edges
                     linewidth=1,  # Width of base map's edge lines
                     zorder=1  # Plot base map edges above the voronoi regions
                     )


# Import shapely to convert string lat-longs to Point objects
from shapely.geometry import Point

# Setup Geopandas Dataframe
def make_gdf(cps_df):
    # Assumes data stored in pandas DataFrame df
    geometry = [Point(xy) for xy in zip(cps_df.School_Longitude, cps_df.School_Latitude)]
    gdf = gpd.GeoDataFrame(cps_df, geometry=geometry)
    return gdf

# Create gdf
gdf = make_gdf(cps_df)

# Set the map projection
proj = geoplot.crs.AlbersEqualArea() #central_longitude=-98, central_latitude=39.5
    
# Display map
display_map(gdf, chicago, proj)

# TO DO: maps well, but how to grab features of voronois?


###############################################################################
# FIND VORONOIS (plots a map and gets bounds?)
###############################################################################
# from: https://github.com/WZBSocialScienceCenter/geovoronoi
from geovoronoi import voronoi_regions_from_coords

points = np.array(list(cps_df.coordinates))
chicago_bounds = chicago.iloc[0].geometry

# TO DO: gets error abour hull distance or something
poly_shapes, pts, poly_to_pt_assignments = voronoi_regions_from_coords(points, 
                                                                       chicago_bounds)

###############################################################################
vor = Voronoi(points)
voronoi_plot_2d(vor)

new_point = [50, 50]   
plt.plot(new_point[0], new_point[1], 'ro')

point_index = np.argmin(np.sum((points - new_point)**2, axis=1))
ridges = np.where(vor.ridge_points == point_index)[0]
vertex_set = set(np.array(vor.ridge_vertices)[ridges, :].ravel())
region = [x for x in vor.regions if set(x) == vertex_set][0]

polygon = vor.vertices[region]
plt.fill(*zip(*polygon), color='yellow')  
plt.show()
