# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 16:37:40 2019

@author: leatr

Copies the georeferencement of a base raster image onto a non-georeferenced
.tiff file; is useful to georeference a binary image based on the original
orthomosaic, for example.
"""
###############################################################################
#################################### ENV ######################################
###############################################################################

import rasterio as rio

###############################################################################
################################### PARAM #####################################
###############################################################################

# get the original tiff file that is georeferenced
original_file = r'D:/LEA/2018MEMURO_sugarbeat_field1/sugarbeat_memuro_field1_20180608_P4RGB_30m_transparent_mosaic_group1.tif'
# open with rasterio the tiff file that we want to georeference
new_file = r'D:/LEA/2018MEMURO_sugarbeat_field1/MASK_sugarbeat_memuro_field1_20180608_P4RGB_30m_transparent_mosaic_group1.png'
# outfile name
out_path = r"D:/LEA/2018MEMURO_sugarbeat_field1/GEOREF_memuro_field1_20180608.tif"

###############################################################################
#################################### CODE #####################################
###############################################################################

original = rio.open(original_file)
new_array_f = rio.open(new_file)

# copy the metadata from the original
new_meta = original.meta.copy()
# replace the no data value to have a clean mask
new_meta.update({'nodata': 0})
# number of iteration needed based on the number of channels of the original
channels = new_array_f.meta['count']
new_meta.update({'count':channels})
# open the new file with original metadata
with rio.open(out_path, 'w', **new_meta) as outf:
    # iterate for all channels
    for k in range(1, channels + 1):
        # read the band
        new_array = new_array_f.read(k)
        # write the band
        outf.write(new_array, k)