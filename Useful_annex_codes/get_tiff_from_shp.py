# -*- coding: utf-8 -*-
"""
Created on Sun Jan  6 21:31:35 2019

@author: leatr

Crops the inputted raster according to individual *.shp files using rasterio
and Fiona (no GDAL).
"""
###############################################################################
################################# ENVIRONMENT #################################
###############################################################################

import fiona, rasterio, rasterio.mask, os, sys
from pathlib import Path

###############################################################################
#################################### INPUTS ###################################
###############################################################################

# Path to the image to cut
inraster = Path(r'D:/LEA/2017MEMURO_sugarbeat_hybrid/sugarbeat_hybrid_memuro_20170531_Ins1X5Raw_30m_transparent_mosaic_group1.tif')
# Path to the _folder_ containing the shapefiles to cut the image with
file_shp = Path(r'D:/LEA/2017MEMURO_sugarbeat_hybrid/Micro_plots_sugarbeat_hybrid_memuro_20170531_Ins1X5Raw_30m_transparent_mosaic_group1/SHP_files')
# Path to the folder where the cut images will be saved
output_folder  = Path(r'D:\LEA\2017MEMURO_sugarbeat_hybrid\IOU\Program_made_plots')
# Crop to the bounding box? True or False
bounding_box = False

###############################################################################
##################################### CODE ####################################
###############################################################################

if os.path.isdir(output_folder) == False:
    os.makedirs(output_folder)
    print(str(output_folder) + ' has been created.')

for k in os.listdir(file_shp):
    if not '.shp' in k:
        pass
    else:
        inshape = os.path.join(file_shp, k)
        
        # get the shp and make a polygon out of it
        with fiona.open(inshape, "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]

        if bounding_box == False:
            # apply the polygon to the raster
            with rasterio.open(inraster) as src:
                out_image, out_transform = rasterio.mask.mask(src, features,
                                                                    crop = False)
                out_meta = src.meta.copy()
        elif bounding_box == True:
            try:
                with rasterio.open(inraster) as src:
                    out_image, out_transform = rasterio.mask.mask(src, features,
                                                                    crop = True)
                    out_meta = src.meta.copy()
                    out_meta['height'] = out_image.shape[1]
                    out_meta['width'] = out_image.shape[2]
            except ValueError:
                sys.exit('''--- The shapefile does not overlap the raster. Please
make sure the inputs are correct and the raster is georeferenced.''')
                
        else :
            sys.exit('''--- Make sure you inputted either True or False 
for the parameter "bounding_box".''')

        # save the output in a new file
        output_name = os.path.join(output_folder, k.replace('.shp','.tiff'))
        with rasterio.open(output_name, "w", **out_meta) as dest:
            dest.write(out_image)
        print('Image cut; available at: ' + output_name)
