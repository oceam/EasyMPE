# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 15:45:21 2019

@author: leatr

Outputs geo-coordinates of the inputted individual *.shp files in the form of a
text file, 4 corners per line. Does not put an identificator or anything in
front of it, takes the files in a pythonic order
(see os.listdir(your_shp_folder) to know this order).
"""

###############################################################################
#################################### ENV ######################################
###############################################################################

import shapefile
from pathlib import Path

###############################################################################
################################## INPUTS #####################################
###############################################################################

# where all the shp files are
shp_folder = Path(r'D:/LEA/2017TANASHI_soybean/soybean3NWEI/soybean_tanashi_3N_20170710_Ins2RGB_15m/Micro_plots_soybean_tanashi_3N_20170710_Ins2RGB_15m_transparent_mosaic_group1/SHP_files')
# where to save the output txt file
main_folder = Path(r'D:\LEA\2017TANASHI_soybean\IOU')
# how to name the output file [i.e. program_made or handmade]
TYPE = 'prog_made_cgs'

###############################################################################
################################### CODE ######################################
###############################################################################

files = list(shp_folder.glob('*.shp'))
with open(main_folder / str('coordinates_' + TYPE + '.txt'), 'w') as f:
    for k in range(len(files)):
        shp = shapefile.Reader(str(files[k])) #open the shapefile
        poly = shp.shapes() # get the polygon
        points = poly[0].points # get the coordinates of the polygon
        # make sure you have the coordinates in the same order every time
        points = points[:-1]
        points = sorted(points)
        ordered_points = points.copy()
        ordered_points[2], ordered_points[3] = points[3], points[2]
        ordered_points = [(int(x), int(y)) for x, y in ordered_points]
        f.write(str(k) + ' ; ' + str(ordered_points) + '\n')
