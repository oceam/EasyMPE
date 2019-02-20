# -*- coding: utf-8 -*-
"""
2019, L. Tresch for University of Tokyo, Field Phenomics Research Laboratory
Please read the read_me.txt for furter information.
Annex code to MPE_main.py

Reverse calculation code is based on Pix4D outputs and Pix4D explanations.
"""
###############################################################################
##################################### ENV #####################################
###############################################################################

import numpy as np
import rasterio
import rasterstats as rs

###############################################################################
##################################### CODE ####################################
###############################################################################

def ReverseCalculation(folder, DSM, offset, PMat, rawImgFold):
    '''Used in "Application" from the class "MainWindow" of MPE_MAIN.py
    Contains all the code to reverse calculate the images
    
    Input : 5
    folder : Path
        absolute path to the active folder containing all the previous
        outputs (more particularly the micro plots corners' coordinates)
    DSM : Path
        absolute path to the DSM file
    offset : Path
        absolute path to the offset file
    PMat : Path
        absolute path to the PMatrix file
    rawImgFold : Path
        absolute path to the folder containing raw drone images'''
    
    # get corners' coordinates files
    csv_georef = folder / 'Intersection_points_georeferenced.csv'
    
    # read the coordinates file
    geo_coords = np.loadtxt(csv_georef, dtype = float, delimiter = ';', skiprows = 1)
    coords_id = np.array(geo_coords)[:, :2].astype(int)
    geo_coords = np.array(geo_coords)[:,2:10]

    # read the offset file
    offset_x, offset_y, offset_z = np.loadtxt(offset, dtype = float)
    
    # read PMatrix file
    PMatrix_nb = np.loadtxt(PMat, dtype = float, delimiter = None, usecols = (1,2,3,4,5,6,7,8,9,10,11,12,))
    PMatrix_names = np.loadtxt(PMat, dtype = str, delimiter = None, usecols = 0)
    
    # create the list summarizing all outputs
    output_list = []
    
    for k in range(len(coords_id)):
        col, row = coords_id[k]
        
        # get the mean value of z in the considered shp
        current_shp = folder / 'SHP_files' / str('Col_' + str(col).zfill(2) +'_row_' + str(row).zfill(2) +'.shp')
        mean_z = rs.zonal_stats(str(current_shp), DSM, stats = 'mean')[0]['mean']
        
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
            current_img = rawImgFold / PMatrix_names[name]
            # open the original image (open does not load the image into memory)
            src_raw_img = rasterio.open(current_img, mode = "r")
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
    
    # return the csv file name
    return (csv_file)


