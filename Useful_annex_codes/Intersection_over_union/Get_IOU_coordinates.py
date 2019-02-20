# -*- coding: utf-8 -*-
"""
Created on Sun Jan  6 12:23:21 2019

@author: leatr

get the 4 coordinates of the MPE microplots (to use on the folder
“Plot_rows_original_whole” i.e. with a black background of the whole image) by
opening the image and finding a bounding box.
"""
###############################################################################
#################################### ENV ######################################
###############################################################################

import os, cv2, numpy as np
from pathlib import Path

###############################################################################
################################## INPUTS #####################################
###############################################################################
# micro plots folder
folder = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/IOU/Program_made_plots')
# handmade or program?
TYPE = 'program_made_LATEST'
# folder where the txt file will be saved
main_folder = Path(r'D:/LEA/2017MEMURO_sugarbeat_production/IOU')

###############################################################################
################################### CODE ######################################
###############################################################################

nb = 0
print(main_folder)
print(TYPE)
with open(main_folder / str('coordinates_' + TYPE + '.txt'), 'w') as f:
    for k in os.listdir(folder):
        if not '.tiff' in k:
            pass
        img = cv2.imread(str(folder / k))
        coords = np.argwhere(img)
        y0, x0, z = coords.min(axis = 0)
        y1, x1, z = coords.max(axis = 0)
        c = np.where(coords[:,1] == x0)
        y_xmin, x_xmin = coords[int(c[0][0])][0], x0
        c = np.where(coords[:,1] == x1)
        y_xmax, x_xmax = coords[int(c[0][-1])][0], x1
        c = np.where(coords[:, 0] == y0)
        y_ymin, x_ymin = y0, coords[int(c[0][0])][1]
        c = np.where(coords[:, 0] == y1)
        y_ymax, x_ymax = y1, coords[int(c[0][-1])][1]
        f.write(str(nb) + ' ; ' + str([(y_ymin, x_ymin), (y_xmax, x_xmax), (y_ymax, x_ymax), (y_xmin, x_xmin)]) + '\n')
        nb += 1