# -*- coding: utf-8 -*-
"""
Created on Sun Jan  6 09:03:21 2019

@author: leatr

calculate the Intersection Over Union ratio based on specific inputs
Text file must have 8 columns as:
    y_1, x_1, y_2, x_2, y_3, x_3, y_4, x_4
which can be obtained by running:
    - Get_IOU_coordinates.py over the Plot_original_whole folder of the EasyMPE
    output
    - get_coordinates_from_shp.py over the SHP_files folder of the EasyMPE output
    (georeferenced coordinates will be outputted, which might be less precise as
    the coordinates will not have decimals)
"""
###############################################################################
#################################### ENV ######################################
###############################################################################

from shapely.geometry import Polygon
import numpy as np
from path import Path

###############################################################################
################################## INPUTS #####################################
###############################################################################

FIELDNAME = '2017_Memuro_production_LATEST'

f_prog = open(r'D:/LEA/2017MEMURO_sugarbeat_production/IOU/coordinates_program_made_LATEST.txt', 'r')
box_prog = f_prog.readlines()

f_hand = open(r'D:/LEA/2017MEMURO_sugarbeat_production/IOU/coordinates_handmade_LATEST.txt', 'r')
box_handmade = f_hand.readlines()

###############################################################################
#################################### CODE ######################################
###############################################################################

def intersection_over_union(boxA, boxB):
    # use coordinates to make a linear ring
    a = Polygon(boxA)
    b = Polygon(boxB)
    # get the intersection of both box
    inter = a.intersection(b).area
    # and the union
    union = a.union(b).area
    #calculate the inter over union percent
    iou = inter/union 
    iou = "%.3f" % iou
    # return
    return (a.area, b.area, "%.3f" % inter, "%.3f" % union, iou)

rows_csv = []
for k in range(len(box_prog)):
    boxA = eval(box_prog[k][:-1].split(' ; ')[1])
    boxB = eval(box_handmade[k][:-1].split(' ; ')[1])
    A_area, B_area, inter, union, iou = intersection_over_union(boxA, boxB)
    values = [str(k), float(A_area), float(B_area), float(inter), float(union), float(iou)]
    rows_csv.append(values)

csvfile = Path(r'D:\LEA\Semi_automatic_segmentation\IOU_results_and_codes\iou_'+FIELDNAME+'.csv')
np.savetxt(csvfile, rows_csv, delimiter = ';', newline='\n', header = 'Plot;Program_box_area;Handmade_box_area;Intersection;Union;IOU', comments = '', fmt='%s')

f_prog.close()
f_hand.close()
