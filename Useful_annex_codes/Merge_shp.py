# -*- coding: utf-8 -*-
"""
Created on Wed Feb 20 09:23:57 2019

@author: leatr
"""

###############################################################################
##################################### ENV #####################################
###############################################################################

import os
from pathlib import Path
import fiona

###############################################################################
################################### INPUTS ####################################
###############################################################################

# Absolute path to the place where the file will be saved
save_path = Path(r"D:\Microplot_extraction\2017TANASHI_soybean\soybean3NWEI\soybean_tanashi_3N_20170710_Ins2RGB_15m\SAVED_tanashi_20170710")
# Name of the output file
output_name = 'Merged'
# Absolute path to the folder containing all the individual *.shp files
folder = Path(r'D:\Microplot_extraction\2017TANASHI_soybean\soybean3NWEI\soybean_tanashi_3N_20170710_Ins2RGB_15m\SAVED_tanashi_20170710\SHP_files')

###############################################################################
##################################### CODE ####################################
###############################################################################

save_path = save_path / str(output_name + '.shp')
files = os.listdir(folder)
files = [str(folder / f) for f in files if '.shp' in f]

meta = fiona.open(files[0]).meta
n = 0
with fiona.open(save_path, 'w', **meta) as output:
    for k in files:
        n += 1
        with fiona.open(k) as f:
            for features in f:
                output.write(features)
                