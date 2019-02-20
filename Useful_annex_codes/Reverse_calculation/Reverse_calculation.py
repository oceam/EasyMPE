# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 10:52:42 2019

@author: leatr

This code does reverse calculation based on cvs files out of the MPE program.
(i.e. organized as : 
    Column;Row;pt1_x;pt1_y;pt2_x;pt2_y;pt3_x;pt3_y;pt4_x;pt4_y )
It outputs a csv file containing the column and row numbers, the name of the raw
image and the pixel coordinates of the designated plot.
"""

###############################################################################
################################ ENVIRONMENT ##################################
###############################################################################

import rasterio as rio
import numpy as np
from path import Path
import rasterstats as rs

###############################################################################
################################### INPUTS ####################################
###############################################################################

###### PIX4D FILES
# dsm file
dsm_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Reverse_calculation_files/sugarbeat_memuro_field2_20180605_P4RGB_30m_dsm.tif')
# offset file
offset_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Reverse_calculation_files/sugarbeat_memuro_field2_20180605_P4RGB_30m_offset.xyz')
# PMatrix file
pmatrix_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Reverse_calculation_files/sugarbeat_memuro_field2_20180605_P4RGB_30m_pmatrix.txt')

###### MPE OUTPUT FILES
# georeferenced coordinates
geo_coord_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Micro_plots_GEOREF_sugarbeat_memuro_field2_20180605_P4RGB_30m_transparent_mosaic_group1_mask/Intersection_points_georeferenced.csv')
# non georeferenced coordinates
non_geo_coord_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Micro_plots_GEOREF_sugarbeat_memuro_field2_20180605_P4RGB_30m_transparent_mosaic_group1_mask/Intersection_points_non_georeferenced.csv')
# raw image folder

###### OTHERS
raw_img_folder = Path(r'D:\LEA\2018MEMURO_sugarbeat_field2\Reverse_calculation_files\RAW_IMAGES_20190115')
# saving folder
folder = Path(r'D:\LEA\2018MEMURO_sugarbeat_field2\Reverse_calculation_files')

###############################################################################
#################################### CODE #####################################
###############################################################################

# read the coordinates file
geo_coords = np.loadtxt(geo_coord_file, dtype = float, delimiter = ';', skiprows = 1)
coords_id = np.array(geo_coords)[:, :2].astype(int)
geo_coords = np.array(geo_coords)[:,2:10]

# read the offset file
offset_x, offset_y, offset_z = np.loadtxt(offset_file, dtype = float)

# read PMatrix file
PMatrix_nb = np.loadtxt(pmatrix_file, dtype = float, delimiter = None, usecols = (1,2,3,4,5,6,7,8,9,10,11,12,))
PMatrix_names = np.loadtxt(pmatrix_file, dtype = str, delimiter = None, usecols = 0)

# create the list summarizing all outputs
output_list = []

for k in range(len(coords_id)):
    col, row = coords_id[k]
    
    # get the mean value of z in the considered shp
    current_shp = folder / 'SHP_files' / str('Col_' + str(col) +'_row_' + str(row) +'.shp')
    mean_z = rs.zonal_stats(str(current_shp), dsm_file, stats = 'mean')[0]['mean']
    
    # get the georeferenced points and organize them
    all_geo_coords = geo_coords[k]
    all_geo_coords = all_geo_coords.reshape((4, 2))
    # substract the offset
    all_geo_coords[:, 0] = all_geo_coords[:, 0] - offset_x
    all_geo_coords[:, 1] = all_geo_coords[:, 1] - offset_y
    # get the z values
    z_coords = np.array([mean_z - offset_z]*4).reshape(4, 1)
    # concatenate all the needed coordinates
    all_geo_coords = np.concatenate((all_geo_coords, z_coords, np.ones((4, 1))), axis = 1)
            
    for name in range(len(PMatrix_names)):
        current_coord = []
        
        # get the PMatrix values from the designated file for a particular
        # raw image
        pmat = PMatrix_nb[name].reshape((3,4))  
        
        # apply the PMatrix
        new_coord = pmat*[coord.reshape((1,4)) for coord in all_geo_coords]
        
        # get all 4 corners pixel coordinates
        for c in new_coord :
            new_x, new_y, new_z = sum(c[0]), sum(c[1]), sum(c[2])
            u, v = int(new_x / new_z), int(new_y / new_z)
            current_coord.append((u, v))
        current_coord = np.array(current_coord)
        # get maximum and minimum coordinates
        max_u, min_u = np.max(current_coord[:, 0]), np.min(current_coord[:, 0])
        max_v, min_v = np.max(current_coord[:, 1]), np.min(current_coord[:, 1])

    	# build up the next 
        current_img = raw_img_folder / PMatrix_names[name]
        # open the original image (open does not load the image into memory)
        src_raw_img = rio.open(current_img, mode = "r")
        # if the calculated coordinates (bounding box) are in the image
        if 0 < min_u < max_u < src_raw_img.width and 0 < min_v < max_v < src_raw_img.height :
 	    # get all the needed info in separate elements of the list
            current_tmp = [col, row, PMatrix_names[name]] + [item for sublist in current_coord for item in sublist]
            # add it to the general list that will later be saved
            output_list.append(current_tmp)
            src_raw_img.close()
        # if not, then move to the next raw image
        else :
            src_raw_img.close()
            pass
        
# create output file and save it as csv
csv_file = folder / 'reverse_cal_outputs.csv'
np.savetxt(csv_file, output_list, delimiter = ';', newline='\n', header = 'Column;Row;raw_img;pt1_u;pt1_v;pt2_u;pt2_v;pt3_u;pt3_v;pt4_u;pt4_v', comments = '', fmt='%s')

print('File saved at : ' + csv_file)



