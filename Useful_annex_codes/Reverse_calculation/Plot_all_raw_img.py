# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 13:42:20 2019

@author: leatr

This code draws the designated plot's silhouettes from the raw images.
The input csv should be organized as :
    Column;Row;raw_img;pt1_u;pt1_v;pt2_u;pt2_v;pt3_u;pt3_v;pt4_u;pt4_v
i.e. outputs of Reverse_calculation.py or EasyMPE reverse calculation step.
"""

###############################################################################
################################ ENVIRONMENT ##################################
###############################################################################

import numpy as np
from path import Path
import cv2
import random
from itertools import chain

###############################################################################
################################### INPUTS ####################################
###############################################################################

# folder with all the raw drone images
raw_folder = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/Raw_images')

# csv file with the coordinates [reverse_cal_outputs.csv]
coord_file = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/Micro_plots_sugarbeat_production_memuro_20170616_Ins1X5RAW_30m_transparent_mosaic_group1/reverse_cal_outputs.csv')

# folder where to save the output global image
save_folder = Path(r'D:\LEA\2017MEMURO_sugarbeat_production\Micro_plots_sugarbeat_production_memuro_20170616_Ins1X5RAW_30m_transparent_mosaic_group1')

# column number of the wanted micro-plot (int)
col = 0
# row number of the wanted micro-plot (int)
row = 0

###############################################################################
#################################### CODE #####################################
###############################################################################

# load all txt
coords_txt = np.loadtxt(coord_file, dtype = str, delimiter = ';', skiprows = 1)
# only keep the data about the selected col and row
coords_txt = np.array([i for i in coords_txt if (i[0] == str(col) and i[1] == str(row))])
### manipulate the data
# get raw data img name
coords_raw_img = coords_txt[:, 2].tolist()
# get the coord values organized in tuples
coords_txt = np.array(coords_txt[:, 3:11], dtype = int)
coords_values = []
for j in coords_txt:
    coords_values.append([])
    for i in range(0, len(j), 2):
        coords_values[-1].append((j[i], j[i+1]))
# attribute a unique number to each raw img
coords_id = [k for k in range(len(coords_values))]

# get one image shape
img = raw_folder / str(coords_raw_img[0])
shape = cv2.imread(str(img)).shape

# create the new image
img = np.zeros(shape)
# for each raw image coords
nb = -1
for k in coords_values:
    nb += 1
    # get a unique color
    color = tuple([random.randint(0, 255) for k in range(3)])
    # draw the rectangle
    cv2.line(img, k[0], k[1], color, 10) 
    cv2.line(img, k[1], k[2], color, 10)  
    cv2.line(img, k[2], k[3], color, 10) 
    cv2.line(img, k[3], k[0], color, 10)
    
    # get the approximate center of the rectangle
    x = int((k[0][0] + k[1][0] + k[2][0] + k[3][0]) / 4)
    y = int((k[0][1] + k[1][1] + k[2][1] + k[3][1]) / 4)
    # add the unique id to know to what raw the rectangle refers to
    # the text is written in a corner of the rectangle 
    cv2.putText(img, str(coords_id[nb]), (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                5, color = color, thickness = 10)

# save the image
img_name = str(save_folder / str('All_raw_images_col_' + str(col) + '_row_'
                                 + str(row) + '.png'))
cv2.imwrite(img_name, img)     

### save the related coordinates file
# make the appropriate array
coords_id = np.array([coords_id]).T
coords_raw_img = np.array([coords_raw_img]).T
coords_values = np.array([list(chain.from_iterable(e)) for e in coords_values])
all_data = np.concatenate((coords_id, coords_raw_img, coords_values), axis = 1)
# get the file name
csv_name = str(save_folder / str('All_raw_images_col_' + str(col) + '_row_'
                                 + str(row) + '_coordinates.csv'))
# save
com = str('Plot : col ' + str(col) + ', row ' + str(row) + '\n')
np.savetxt(csv_name, all_data, delimiter = ';', newline='\n', 
           header = 'id;raw_img;pt1_u;pt1_v;pt2_u;pt2_v;pt3_u;pt3_v;pt4_u;pt4_v', 
           comments = com, fmt='%s')



      
       
    


