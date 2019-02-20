# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 10:52:56 2019

@author: leatr

Outputs individual *.shp files based on the input text file containing
coordinates and a reference raster with the associated georeference system.
"""
###############################################################################
#################################### ENV ######################################
###############################################################################

import rasterio as rio
from path import Path
import shapefile

###############################################################################
################################### PARAM #####################################
###############################################################################

### make shapefiles based on a coordinates file
# Original raster from which the geo-referencement will be copied
original = rio.open(r'D:/LEA/2018MEMURO_sugarbeat_field2/sugarbeat_memuro_field2_20180605_P4RGB_30m_transparent_mosaic_group1.tif')

# where to save the output
folder = Path(r'D:\LEA\2018MEMURO_sugarbeat_field2\Results_handmade')

# the coordinates file organized as: Column;Row;pt1_x;pt1_y;pt2_x;pt2_y;pt3_x;pt3_y;pt4_x;pt4_y
file_pts = open(r'D:/LEA/2018MEMURO_sugarbeat_field2/SAVED_Micro_plots_sugarbeat_memuro_field2_20180605_P4RGB_30m_transparent_mosaic_group1_mask/Intersection_points.csv', 'r')
all_file_pts = file_pts.readlines()

###############################################################################
#################################### CODE #####################################
###############################################################################

aff = original.transform
points = []
pts = []
for k in range(1, len(all_file_pts)):
    liste = all_file_pts[k].split(';')[2:-1]
    pts.append([(float(liste[0]), -1*float(liste[1])),(float(liste[2]), -1*float(liste[3])),
                (float(liste[4]), -1*float(liste[5])),(float(liste[6]), -1*float(liste[7]))]) 

nbCol, nbRow = 0, 0
for i in pts:
    points = []
    for k in i:
        points.append(k*aff)
    points.append(points[0])
    
    ### make a shapefile
    save_path = folder / str('Col_' + str(nbCol) + '_row_' + str(nbRow) + '.shp')
    print(save_path)
    print(type(save_path))
    # write a new shp file as a polygon shape
    w = shapefile.Writer(str(save_path), shapeType = 5)
    # geometry
    w.poly([points])
    # fields definition
    w.field('Col_nb','N', '40')
    w.field('Row_nb','N', '40')
    w.record(int(nbCol), int(nbRow))
    w.close()
    nbRow += 1
    if nbRow == 27:
        nbCol += 1
        nbRow = 0
