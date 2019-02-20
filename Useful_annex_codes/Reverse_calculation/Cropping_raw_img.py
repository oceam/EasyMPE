# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 15:46:44 2019

@author: leatr

This code crops the designated plot from the indicated raw drone image.
The csv can either come from :
- reverse_calculation.py (csv output).
    The csv should be organized as follows :
    Column;Row;raw_img;pt1_u;pt1_v;pt2_u;pt2_v;pt3_u;pt3_v;pt4_u;pt4_v
- plot_all_img.py
    The csv header should be as follows :
    Plot : col 0, row 0
    id;raw_img;pt1_u;pt1_v;pt2_u;pt2_v;pt3_u;pt3_v;pt4_u;pt4_v
"""

###############################################################################
################################ ENVIRONMENT ##################################
###############################################################################

import numpy as np
from path import Path
import cv2

###############################################################################
################################### INPUTS ####################################
###############################################################################

# folder with all the raw drone images
raw_folder = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/Raw_images')

# csv file with the coordinates
coord_file = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/Micro_plots_sugarbeat_production_memuro_20170616_Ins1X5RAW_30m_transparent_mosaic_group1/reverse_cal_outputs.csv')
#coord_file = Path(r'D:/LEA/2018MEMURO_sugarbeat_field2/Reverse_calculation_files/All_raw_images_col_0_row_0_coordinates.csv')

# folder where the masked image will be saved
save_folder = Path(r'D:\LEA\2018MEMURO_sugarbeat_field2\Reverse_calculation_files')

# column number of the wanted micro-plot (int)
col = 0
# row number of the wanted micro-plot (int)
row = 0

# does the csv file comes from "reverse_calculation" or "plot_all_raw_img" ?
csv_origin = 'reverse_calculation'
#csv_origin = 'plot_all_img'

##### if the coordinates come from "reverse_calculation" :
# wanted raw image name (as in the csv file), type : str
# ex : raw_img_id = 'DJI_0025.JPG'
raw_img_id = 'DJI_0106.JPG'

#### if the coordinates come from "plot_all_img.py"
# id number (as in the csv file), type : int
# ex : id_img = 11
id_img = 11

###############################################################################
#################################### CODE #####################################
###############################################################################

# get the coordinates in both cases
if csv_origin == 'reverse_calculation':
    raw_img_names = np.loadtxt(coord_file, dtype = str, delimiter = ';', skiprows = 1,
                               usecols = 2).tolist()
    indice = raw_img_names.index(raw_img_id)
    coords = np.loadtxt(coord_file, dtype = int, delimiter = ';', skiprows = 1,
                             usecols = (3, 4, 5, 6, 7, 8, 9, 10))[indice]
    
elif csv_origin == 'plot_all_img':
    id_names = np.loadtxt(coord_file, dtype = int, delimiter = ';', skiprows = 2,
                               usecols = 0).tolist()
    indice = id_names.index(id_img)
    coords = np.loadtxt(coord_file, dtype = int, delimiter = ';', skiprows = 2,
                             usecols = (2, 3, 4, 5, 6, 7, 8, 9))[indice]
    raw_img_id = np.loadtxt(coord_file, dtype = str, delimiter = ';', skiprows = 2,
                             usecols = (1))[indice]
else :
    print('''Please write either "reverse_calculation.py" or "plot_all_img.py"
          for the csv_origin paramater.''')
    
# get coordinates in tuples
roi_corners = np.array([[(coords[0], coords[1]), (coords[2], coords[3]),
                         (coords[4], coords[5]), (coords[6], coords[7])]])
# read the base raw image
raw_img_path = raw_folder / raw_img_id
# create a black img of the same shape
raw_img = cv2.imread(raw_img_path)
# create the mask that will be applied, based on roi_corners values
mask = np.zeros(raw_img.shape, dtype = np.uint8)
cv2.fillPoly(mask, roi_corners, (255, 255, 255))
# apply the mask
masked_img = cv2.bitwise_and(raw_img, mask)       
# saving the img
output_path = save_folder / str('Col_' + str(col) + '_row_' + str(row) + 
                                '_from_' + raw_img_id)
cv2.imwrite(output_path, masked_img)
print('Done. \nOutput file at :')
print(str(output_path))
    
