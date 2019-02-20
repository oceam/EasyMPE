# -*- coding: utf-8 -*-
"""
2019, L. Tresch for University of Tokyo, Field Phenomics Research Laboratory
Please read the read_me.txt for furter information.
Annex code to MPE_main.py

"""
### ENVIRONMENT
import numpy as np
import cv2, os, math
from skimage.morphology import extrema
from skimage import  morphology
import shapefile, fiona
    
def MPE(img, folder, original_img, YN_binary, nbOfRowPerPlot, 
        nbOfColumnPerPlot, globalOrientation, noise, field_image, aff, 
        y_offset, x_offset):
    ''' Identifies and crop the columns and the rows of the field.
    
    12 inputs:
        img: array of lists
            Binary image of the original image read in openCV
        folder: path
            Absolute path to the folder in which all is saved
        original_img: array of lists
            Original image read in openCV
        YN_binary: bolean
            Equals True if the original image is a binary
        nbOfRowPerPlot: int
            Number of row per microplot
        nbOfColumnPerPlot: int
            Number of column per microplot
        globalOrientation: str ('V' or 'H')
            Global orientation of the column as inputted by the user
        noise: int
            Noise removal value
        field_image: Path object
            absolute path to the original image
        aff: Affine object OR int (0)
            Affine transformation matrix associated with the original image
            georeferencement, project the calculated points into its CRS
            Equals zero if the original image is not georeferenced
        y_offset: int
            The vertical distance that has been cropped and should be considered
            for the coordinates calculation
        x_offset: int
            The horizontal distance that has been cropped and should be considered
            for the coordinates calculation
        
    Outputs: none
    Returns number if there is an error which will trigger a pop up displaying
    a message.
    Returns 'OK' if the end has been reached.
    
    '''

    #######################################################################
    ####################### ROTATE THE BINARY IMAGE #######################
    #######################################################################
    

    # get all coordinates of the white pixels i.e. plants
    coords_angle = np.column_stack(np.where(img > 0))
    # use these coordinates to compute a rotated bounding box that contains all
    # coordinates
    angle = cv2.minAreaRect(coords_angle)[-1]
    # the 'cv2.minAreaRect' function returns values in the
    # range [-90, 0[ ; we want it positive
    if angle < -45:
    	angle = -(90 + angle)     
    # otherwise, just take the inverse of the angle to make
    # it positive
    else:
    	angle = -angle
    # if the rows are orginally horizontal, we want them to become vertical
    if globalOrientation == 'H':
        angle += 90

    print('ANGLE: ' + str(angle))
    
    img_binary = img.copy()
    img_rotated, add_y, add_x = rotate_bound(img.astype(np.uint8), angle, change_bigger = True)
    cv2.imwrite(str(folder / 'Binary_straight.jpg'), img_rotated)

    # make a skeleton of the binary image so that clusters will be in the
    # middle of the rows, then erode and dilate to erase weeds and connect
    # broken lines
    # parameters (horizontal array)
    param_binaryErosion = np.ones((1, 20))
    param_skeletonErosion = np.ones((1, 5))
    param_skeletonDil = np.ones((1, 100))
    # application
    binary_erode = morphology.binary_erosion(img_rotated, selem = param_binaryErosion)
    skeleton = morphology.skeletonize((binary_erode*1).astype(np.uint8))*255
    cv2.imwrite(str(folder / 'Skeleton_original.jpg'), skeleton)
    skeleton = morphology.binary_erosion(skeleton, selem = param_skeletonErosion)
    skeleton = morphology.binary_dilation(skeleton, selem = param_skeletonDil)*255
    cv2.imwrite(str(folder / 'Skeleton_manipulated.jpg'), skeleton)
   
    
    #######################################################################
    ########################### GET THE COLUMNS ###########################
    #######################################################################
    
    # get local maxima on the whole binary picture
    local_maxima = extrema.local_maxima(skeleton)
    # sum the number of local maxima into a one-line array (i.e. number of
    # maxima in each column)
    sum_maxima = np.sum(local_maxima, axis = 0).astype(float)
    # make a copy
    sum_maxima_nan = sum_maxima.copy()
    # replace 0 with NaN
    sum_maxima_nan[sum_maxima == 0] = np.nan
    # get the average number of maxmima for a column
    mean_line = np.nanmean(sum_maxima_nan)
    # erase all the values smaller than 1/3 of the average
    sum_maxima[sum_maxima < mean_line/3] = 0
    # draw the columns and save the corner points of each column area
    img, cut_points, col_w, img_core_col = draw_separation_lines(sum_maxima, 
                                                             rows_img = img_rotated,
                                                             col = True) 
    
    # if no points have been detected, it means the code is not working as it is
    if cut_points == []:
        return ('1')
    
    # save the image with the columns delimited
    cv2.imwrite(str(folder / 'Binary_columns_straight.jpg'), img)
    cv2.imwrite(str(folder / 'Binary_core_columns.jpg'), img_core_col)

    
    ## rotate the points of the separation lines and get the lines equations 
    center = (img_binary.shape[0]/2, img_binary.shape[1]/2)
    cut_points = np.array(cut_points)
    # subtraction of the black pixels which had been added for the rotation
    cut_points[:, :, 0] = cut_points[:, :, 0] - add_x
    cut_points[:, :, 1] = cut_points[:, :, 1] - add_y
    # rotate the points back into the original angle
    cut_points = rotate(center, cut_points, math.radians(angle))
    # get the line equations from points
    columns_a, columns_b = get_equations(cut_points)
    # rotate back the core column image
    img_core_col, _, _ = rotate_bound(img_core_col, -1*angle)
    y = int((img_core_col.shape[0] - img_binary.shape[0])/2)
    x = int((img_core_col.shape[1] - img_binary.shape[1])/2)
    img_core_col = img_core_col[y:-y, x:-x]
    img_core_col = cv2.resize(img_core_col, img_binary.shape[::-1]) 
    cv2.imwrite(str(folder / 'Binary_core.jpg'), img_core_col)
    
    ## cut the columns
    # create all the needed directories / check if existent / delete if necessary
    if YN_binary == False:
        sub_folder_columnOriginal = folder / str('Plot_columns_original')
    sub_folder_columnBinary = folder / str('Plot_columns_binary')
    sub_folder_columnCoreBinary = folder / str('Plot_columns_core')
    if not(sub_folder_columnBinary.is_dir()):
        if YN_binary == False:
            sub_folder_columnOriginal.mkdir()
        sub_folder_columnBinary.mkdir()
        sub_folder_columnCoreBinary.mkdir()
    # initialization
    maxY, maxX = img_binary.shape
    c = str(0).zfill(2) # only exists for saving names
    # for every detected column, with a step defined by the inputted number
    # nbOfColumnPerPlot in the GUI
    for k in range(0, len(columns_a), nbOfColumnPerPlot):
        # try first as it is (i.e. with that step value)
        try:
            n = nbOfColumnPerPlot - 1 #bc we want the end line
            pt1 = ((0 - columns_b[k][0])/columns_a[k][0], 0)
            pt2 = ((0 - columns_b[k + n][1])/columns_a[k + n][1], 0) #could have done [k+n+1][0] -> equivalent
            pt3 = ((maxY - columns_b[k + n][1])/columns_a[k + n][1], maxY)
            pt4 = ((maxY - columns_b[k][0])/columns_a[k][0], maxY)
            # all 4 points of one column, counter clock wise
            roi_corners = np.array([[pt1, pt2, pt3, pt4]], dtype = np.int32)
            # make a mask and crop out the current column
            mask = np.zeros(img_binary.shape, dtype = np.uint8)
            cv2.fillPoly(mask, roi_corners, (255,))
            if YN_binary == False:
                column_original = cv2.bitwise_and(original_img, original_img, mask = mask)
                cv2.imwrite(str(sub_folder_columnOriginal / str('Plot_column_' + c + '_cropped.jpg')), column_original)
            # apply the mask and save the images
            column_binary = cv2.bitwise_and(img_binary, img_binary, mask = mask)   
            cv2.imwrite(str(sub_folder_columnBinary / str('Plot_column_'+ c +'_cropped.jpg')), column_binary)
            column_core = cv2.bitwise_and(img_core_col, img_core_col, mask = mask)
            cv2.imwrite(str(sub_folder_columnCoreBinary / str('Plot_column_' + c + '_cropped.jpg')), column_core)
            c = str(int(c) + 1).zfill(2)
        # if the number inputed is not proportional to the detected number of columns
        # then do one by one for what is left
        except IndexError: 
            # same as before but one detected column at a time
            for i in range(k, len(columns_a)):
                pt1 = ((0 - columns_b[i][0])/columns_a[i][0], 0)
                pt2 = ((0 - columns_b[i][1])/columns_a[i][1], 0)
                pt3 = ((maxY - columns_b[i][1])/columns_a[i][1], maxY)
                pt4 = ((maxY - columns_b[i][0])/columns_a[i][0], maxY)
                # 4 column points, counter clockwise
                roi_corners = np.array([[pt1, pt2, pt3, pt4]], dtype = np.int32)
                # mask making
                mask = np.zeros(img_binary.shape, dtype = np.uint8)
                cv2.fillPoly(mask, roi_corners, (255,))
                if YN_binary == False:
                    column_original = cv2.bitwise_and(original_img, original_img, mask = mask)
                    cv2.imwrite(str(sub_folder_columnOriginal / str('Plot_column_' + str(c) + '_cropped.jpg')), column_original)
                # applying mask and saving images
                column_binary = cv2.bitwise_and(img_binary, mask)   
                cv2.imwrite(str(sub_folder_columnBinary / str('Plot_column_'+ str(c) +'_cropped.jpg')), column_binary)
                column_core = cv2.bitwise_and(img_core_col, img_core_col, mask = mask)
                cv2.imwrite(str(sub_folder_columnCoreBinary / str('Plot_column_' + c + '_cropped.jpg')), column_core)
                c = str(int(c) + 1).zfill(2)
        
    #######################################################################
    ############################# GET THE ROWS ############################
    #######################################################################
    
    # new angle to get the ROWS in a vertical state (i.e. columns are 
    # oriented horizontally)
    angle_horiz = angle + 90
    print('Horizontal angle : ' + str(angle_horiz))
    
    # get all the files from the previous part, i.e. *binary* columns
    files = list(sub_folder_columnCoreBinary.glob('*.jpg'))
    # make all the necessary folders etc
    sub_folder_horizontalColumn = folder / 'Horizontal_columns'
    if YN_binary == False:
        sub_folder_rowOriginal = folder / str('Plot_rows_original')
        sub_folder_rowOriginalWhole = folder / str('Plot_rows_original_whole')
    else:
        sub_folder_rowOriginalWhole = folder / str('Plot_rows_binary_whole')
    sub_folder_rowBinary = folder / str('Plot_rows_binary')
    sub_folder_SHP = folder / str('SHP_files')
    if not(sub_folder_horizontalColumn.is_dir()):
        sub_folder_horizontalColumn.mkdir()
        if YN_binary == False:
            sub_folder_rowOriginal.mkdir()
            sub_folder_rowOriginalWhole.mkdir()
        sub_folder_rowBinary.mkdir()
        sub_folder_SHP.mkdir()
    
    # initialization
    maxY, maxX = img.shape
    nbOfRowPerColumn = 0
    intersection, intersection_geo = [], []
    nbOfColumn = len(columns_a)
    # for every file in the column file
    for nb in range(0, len(files)):
        # get the column number
        nb_column = str(nb).zfill(2)
        ## identify the rows
        # read the column file
        file_img = cv2.imread(str(files[nb]), 0)
        # rotate it until the column is horizontally oriented
        column_binary_rotate, add_y, add_x = rotate_bound(file_img, angle_horiz, change_bigger = True)
        # make the sum of all white pixels on one line
        sum_rows = np.sum(column_binary_rotate, axis = 0).astype(float)
        # make a copy and replace 0 by nan to get the mean value of the sum without 0
        sum_rows_nan = sum_rows.copy()
        sum_rows_nan[sum_rows == 0] = np.nan
        mean_line = np.nanmean(sum_rows_nan)
        # erase the values smaller than half of the mean
        sum_rows[sum_rows < mean_line/2] = 0
        # identify the rows with the changing pattern
        _, cut_points, w = draw_separation_lines(np.array(sum_rows), 
                                                 rows_img = column_binary_rotate)

        # if not separation lines has been detected, the code is not working
        # as it is
        if cut_points == []:
        # save the output image with separation lines for rows
            return('2')
        cv2.imwrite(str(sub_folder_horizontalColumn / str('Rows_horizontal_delimited_column_' + str(nb_column) + '.jpg')), column_binary_rotate)
        
        ## get the points in the original angle
        # original center
        center = (img_binary.shape[0]/2, img_binary.shape[1]/2)
        cut_points = np.array(cut_points)
        # points without the added black border (in rotate_bound)
        cut_points[:, :, 0] = cut_points[:, :, 0] - add_x
        cut_points[:, :, 1] = cut_points[:, :, 1] - add_y
        # rotate the points
        cut_points = rotate(center, cut_points, math.radians(angle_horiz))
        # get equations based on the points
        rows_a, rows_b = get_equations(cut_points)
                
        # initialization of various counts
        c = str(0).zfill(2) # for file names
        nbStartColumn = nb # start detected column number
        nbEndColumn = int(nbStartColumn) + nbOfColumnPerPlot - 1 # end detected column
        print('Column nb: ' + str(nb_column))

        ### cut the rows
        # read the original column image
        current_column_binary = cv2.imread(str(sub_folder_columnBinary / files[nb].name), 0)
        if YN_binary == False:
            current_column_original = cv2.imread(str(sub_folder_columnOriginal / files[nb].name))
        else:
            current_column_original = cv2.imread(str(sub_folder_columnBinary / files[nb].name), 0)
            
        # get the number of rows in this column
        nbOfRowPerColumn += len(rows_a)
        
        # for every row in that column, with a step defined by the inputted
        # number nbOfRowPerPlot in the GUI
        for k in range(0, len(rows_a), nbOfRowPerPlot):
            # try with this step first
            try:
                ### get the cut points of the row
                n = nbOfRowPerPlot - 1 # bc we want the end line of the end row
                pt1 = ((0 - rows_b[k][0])/rows_a[k][0], 0)
                pt2 = ((0 - rows_b[k + n][1])/rows_a[k + n][1], 0) #[k+n+1][0] would NOT be equivalent
                pt3 = ((maxY - rows_b[k + n][1])/rows_a[k + n][1], maxY)
                pt4 = ((maxY - rows_b[k][0])/rows_a[k][0], maxY)
                # get all the points counter-clockwise
                roi_corners = np.array([[pt1, pt2, pt3, pt4]], dtype = np.int32)
                # fill a mask
                mask = np.zeros(file_img.shape, dtype = np.uint8)
                cv2.fillPoly(mask, roi_corners, (255,))
                # apply the mask to the column images (binary)
                row_binary = cv2.bitwise_and(current_column_binary, mask)  
                cv2.imwrite(str(sub_folder_rowBinary / str('Plot_column_' + str(nb_column) + '_row_'+ str(c) + '_cropped.jpg')), row_binary)
                # use a bounding box to only get the wanted part of the original
                # image i.e. the row and not all the black pixels around
                row_original = cv2.bitwise_and(current_column_original, current_column_original, mask = mask)
                if YN_binary == False:
                    # get the coords for which pixel value =/= 0
                    coords = np.argwhere(row_original)
                    # get the first pixels
                    x0, y0, z = coords.min(axis = 0)
                    # get the last pixels
                    x1, y1, z = coords.max(axis = 0) + 1
                    # crop
                    row_original_cropped = row_original[x0:x1, y0:y1]
                    # save
                    cv2.imwrite(str(sub_folder_rowOriginal / str('Plot_column_' + str(nb_column) + '_row_' + str(c) + '_cropped.jpg')), row_original_cropped)
                    cv2.imwrite(str(sub_folder_rowOriginalWhole / str('Plot_column_' + str(nb_column) + '_row_' + str(c) + '_whole_pic.jpg')), row_original)
                # get the intersection of the lines between the considered
                # column and row (i.e. the 4 cropping points)
                inter, inter_geo = line_intersection(columns_a[nbStartColumn], columns_a[nbEndColumn],
                        columns_b[nbStartColumn], columns_b[nbEndColumn], rows_a[k], rows_a[k + n],
                        rows_b[k], rows_b[k + n], aff, y_offset, x_offset)
                # if the georeferenced points exist
                if type(inter_geo) != type(None):
                    # make the shp files out of the 4 corner points
                    make_shp(sub_folder_SHP, nb_column, c, inter_geo)
                    # prepare the array to be saved
                    inter_geo = [item for sublist in inter_geo for item in sublist]
                    inter_geo.insert(0, c)
                    inter_geo.insert(0, nb_column)
                    intersection_geo.append(inter_geo)
                # if not georeference, use pixel values
                else :
                    # make the shp files out of the 4 corner point
                    make_shp(sub_folder_SHP, nb_column, c, inter)
                # get the points in a 8-elements list (no more tuples)
                inter = [item for sublist in inter for item in sublist]
                # insert row number at the begining
                inter.insert(0, c)
                # insert column number at the beginning
                inter.insert(0, nb_column)
                # "save" the list into "intersection" list
                intersection.append(inter)
                # add up 1 element for the next row
                c = str(int(c) + 1).zfill(2)
            # if the number inputed is not proportional to the detected
            # number of columns, then do one by one for what is left
            except IndexError: 
                for i in range(k, len(rows_a)):
                    pt1 = ((0 - rows_b[i][0])/rows_a[i][0], 0)
                    pt2 = ((0 - rows_b[i][1])/rows_a[i][1], 0)
                    pt3 = ((maxY - rows_b[i][1])/rows_a[i][1], maxY)
                    pt4 = ((maxY - rows_b[i][0])/rows_a[i][0], maxY)
                    roi_corners = np.array([[pt1, pt2, pt3, pt4]], dtype = np.int32)
                    mask = np.zeros(img_binary.shape, dtype = np.uint8)
                    cv2.fillPoly(mask, roi_corners, (255,))
                    row_binary = cv2.bitwise_and(current_column_binary, current_column_binary, mask = mask)   
                    cv2.imwrite(str(sub_folder_rowBinary / str('Plot_column_' + str(nb_column) + '_row_' + str(c) +'_cropped.jpg')), row_binary)
                    row_original = cv2.bitwise_and(current_column_original, current_column_original, mask = mask)
                    if YN_binary == False:
                        coords = np.argwhere(row_original)
                        x0, y0, z = coords.min(axis = 0)
                        x1, y1, z = coords.max(axis = 0) + 1   # slices are exclusive at the top
                        row_original_cropped = row_original[x0:x1, y0:y1]
                        cv2.imwrite(str(sub_folder_rowOriginal / str('Plot_column_' + str(nb_column) + '_row_' + str(c) + '_cropped.jpg')), row_original_cropped)
                        cv2.imwrite(str(sub_folder_rowOriginalWhole / str('Plot_column_' + str(nb_column) + '_row_' + str(c) + '_whole_pic.jpg')), row_original)
                    # get the intersection between column and row considered
                    inter, inter_geo = line_intersection(columns_a[nbStartColumn], columns_a[nbEndColumn], 
                                    columns_b[nbStartColumn], columns_b[nbEndColumn], rows_a[i], rows_a[i],
                                    rows_b[i], rows_b[i], aff, y_offset, x_offset)
                    if type(inter_geo) != type(None):
                        # make the shp files out of the 4 corner points
                        make_shp(sub_folder_SHP, nb_column, c, inter_geo)
                        # prepare the array to be saved
                        inter_geo = [item for sublist in inter_geo for item in sublist]
                        inter_geo.insert(0, c)
                        inter_geo.insert(0, nb_column)
                        intersection_geo.append(inter_geo)
                    # if not georeference, use pixel values
                    else :
                        # make the shp files out of the 4 corner point
                        make_shp(sub_folder_SHP, nb_column, c, inter)
                    inter = [item for sublist in inter for item in sublist]
                    inter.insert(0, c)
                    inter.insert(0, nb_column)
                    intersection.append(inter)
                    c = str(int(c) + 1).zfill(2)
                    
    ### make a shp file with all individual shp merged
    # get all the shp absolute paths
    individual_shp_files = os.listdir(sub_folder_SHP)
    individual_shp_files = [str(sub_folder_SHP / f) for f in individual_shp_files if '.shp' in f]
    # make a shp file with the meta of the individual shp
    meta = fiona.open(individual_shp_files[0]).meta
    # write all the individual shp into the merging file
    with fiona.open(folder / 'All_plots.shp', 'w', **meta) as output:
        for k in individual_shp_files:
            with fiona.open(k) as f:
                for features in f:
                    output.write(features)               
    
    # get the average number of row per column
    nbOfRowPerColumn = nbOfRowPerColumn/nbOfColumn
    # save the metadata
    metadata(folder, field_image, noise, nbOfColumnPerPlot, 
             nbOfRowPerPlot, globalOrientation, sub_folder_rowBinary, sub_folder_SHP, angle, 
             nbOfColumn, nbOfRowPerColumn, intersection, aff, intersection_geo)
    return ('OK')

###############################################################################
################################### ANNEXES ###################################
###############################################################################
    
def rotate_bound(image, angle, change_bigger = None):
    """ Rotate an image, change the size if inputted to makes sure all pixels 
    are still displayed in the output
    
    Inputs : 3
        image : list of list
            image to rotate
        angle : int
            angle by which the image have to be rotated
        change_bigger : None or not None
            None : output image has the same size as input
            else : the size of the image is changed to a square of width of
                the diagonal of the original image (such as any pixel in the 
                original will not shift out of the output after being rotated)
    
    Outputs : 3
        im_out : list of list
            the rotated image
        add_y : int
            half of how many pixels were added on the y-axis (left border, for example)
        add_x : int
            half of how many pixels were added on the x-axis (top border, for example)"""
            
    # get the size of the un-rotated image
    rows, cols = image.shape
    # check if the shape will be changed or not
    if type(change_bigger) != type(None):
        # calculate the diagonal "pixel-distance"
        maxShape = int(np.around(math.sqrt(rows**2 + cols**2)))
        # get how many pixels must be added all around the original image for it
        # to be a square of the width of the original image's diagonal
        add_y = int((maxShape - rows)/2)
        add_x = int((maxShape - cols)/2)
        # add the contour
        image_in = cv2.copyMakeBorder(image, add_y, add_y, add_x, add_x, cv2.BORDER_CONSTANT, value = (0,))
        # new size
        cols, rows = maxShape, maxShape
    else:
        image_in = image
        # no add of contours
        add_y, add_x = 0, 0
    # center coordinates
    cx, cy = int(cols/2), int(rows/2)
    # get the rotation matrix according to the center and the angle
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1)
    # apply the matrix to the image
    im_out = cv2.warpAffine(image_in, M, (cols, rows))
    return im_out, add_y, add_x

def rotate(origin, points, angle):
    """
    Rotate a list of list of 4 points, counterclockwise, by a given angle around
    a given origin. The y axis is considered going downward.
    
    Inputs : 3
        origin : tuple
            coordinates of the origin around which the rotation will be done
        points : list of list of list, as [[[px, py]]]
            points that will be rotated
        angle : int
            angle in radians of the needed rotation
    Output : 1
        points : list of list
            
    """
    oy, ox = origin
    # iterate throught all the elements of points
    for column in range(len(points)):
        for point in range(len(points[column])):
            px, py = points[column][point]
            # rotate the points according to the center and angle
            qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
            qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
            # save the new values
            points[column][point] = int(qx), int(qy)
    return points

def draw_separation_lines(img, rows_img, col = None):
    """ Draw vertical separation lines between clusters than are in different
    areas horizontally (i.e. do not share the same horizontal space)
    
    Input : 
        img : list of list
            image to process
        rows_img : list of list
            image on which to draw
    
    Outputs :
        img : list of list
            image processed, on which separation lines have been drawn
        cut_points : list of list
            coordinates of where the separation lines have been drawn
        width : int
            average width of the distance between the following separation lines
            (average width of the space "columns" between separation lines)
    """
    # get the maximum value of each column in one array of the size [width of
    # the image, 1]
    # all pixels are either 0 (black) or 1 (cluster line) so that when "crushed"
    # all together, similar clusters are considered as one. This is to avoid 
    # broken lines to be treated as several column/row when they belong to the
    # same area
    cut_points, start, end = [], [], []
    if col == True:
        # initialization for later (img with only the core of the column)
        img_core_col = rows_img.copy()
    # search for situations, in the "1-row array crushed image", that shows a
    # change i.e. pixels as : 000001111 or 11110000
    for i in range(len(img) - 1):
        # search for 01 situations
        if img[i] == 0 and img[i+1] != 0:
            # "start" contains all the x positions of start points of a "crushed"
            # cluster merged in the "1-row array crushed image"
            start.append(i)
        # search for 10 situation
        elif img[i] != 0 and img[i+1] == 0:
            # "end" contains all the x positions of end points of a "crushed"
            # cluster merged in the "1-row array crushed image"
            end.append(i)
    cut_points = []
    maxY = img.shape[0]
    img = rows_img
    # if no element has been identified at all (black image, not cluster)
    if len(start) == 0:
        return(img, [], 0)
    # if more than 2 elements has been identified
    elif len(start) > 2:
        # start at the second element and finishes at the second-to-last
        # because first and last are special cases
        for k in range(1, len(start) - 1):
            # save all the start and end points
            cut_points.append([])
            # calculate a margin so that the drawn lines are in the middle of
            # the end line of the previous element and the start line of the 
            # following element (centers lines between elements)
            margin_start = int((start[k] - end[k - 1])/2)
            margin_end = int((start[k + 1] - end[k])/2)
            # change the start coordinate values to the center values using - margin
            cut_points[-1].append((start[k] - margin_start, 0))
            cut_points[-1].append((start[k] - margin_start, maxY))
            # draw the start lines
            cv2.line(img, cut_points[-1][0], cut_points[-1][1], (255,), 3)
            # change the end coordinate values to the center values using + margin
            cut_points[-1].append((end[k] + margin_end, 0))
            cut_points[-1].append((end[k] + margin_end, maxY))
            # draw the end lines
            cv2.line(img, cut_points[-1][2], cut_points[-1][3], (255,), 3)
            # if it is the second element, there is no element before
            if k == 1:
                # for afterwards, value of margin used for the second column is saved
                # (start and end margin of the first column = start margin of the second column)
                margin_firstColumn = margin_start
            if k == len(start) - 2:
                # for afterwards, value of margin used for the second-to-last is saved
                # (start and end margin of the last column = end margin of the
                # second-to-lat column)
                margin_lastColumn = margin_end
            if col == True:
                # erase data outside of the core of the col
                img_core_col[0:maxY, end[k]:start[k+1]] = 0
        # make the same for special cases i.e. add margins and draw first and
        # last separation lines with the values saved before
        margin = margin_firstColumn
        cut_points.insert(0, [(start[0] - margin, 0), (start[0] - margin, maxY), (end[0] + margin, 0), (end[0] + margin, maxY)])
        cv2.line(img, cut_points[0][0], cut_points[0][1], (255,), 3)
        cv2.line(img, cut_points[0][2], cut_points[0][3], (255,), 3)
        if col == True:
            # erase data outside of the core of the first col (on the left and right)
            img_core_col[0:maxY, 0:start[0]] = 0
            img_core_col[0:maxY, end[0]:start[1]] = 0
        # do last column
        margin = margin_lastColumn
        cut_points.insert(len(cut_points), [(start[-1] - margin, 0), (start[-1] - margin, maxY), (end[-1] + margin, 0), (end[-1] + margin, maxY)])
        cv2.line(img, cut_points[-1][0], cut_points[-1][1], (255,), 3)
        cv2.line(img, cut_points[-1][2], cut_points[-1][3], (255,), 3)
        if col == True:
            # erase data outside of the core of the last col
            img_core_col[0:maxY, end[-1]:end[-1] + margin] = 0
    # if only two elements are detected
    elif len(start) == 2 :
        # the margin is then the center value of second line start position
        # and the first line end position
        margin = (start[1] - end[0])/2
        # calculate the position and draw them
        for i in range(2):
            cut_points.append([(int(start[i] - margin), 0), (int(start[i] - margin), maxY), (int(end[i] + margin), 0), (int(end[i] + margin), maxY)])
            cv2.line(img, cut_points[-1][0], cut_points[-1][1], (255,), 3)
            cv2.line(img, cut_points[-1][2], cut_points[-1][3], (255,), 3)
        if col == True:
            img_core_col[0:maxY, 0:start[0]] = 0
            img_core_col[0:maxY, end[0]:start[1]] = 0
            img_core_col[0:maxY, end[-1]:int(end[-1] + margin)] = 0
    # if one element detected
    else:
        # margin decided arbitrarly : 1/4 of the width of the element
        w = int((end[0] - start[0])/4)
        # separation points are calculated and drawn
        cut_points.append([(start[0] - w , 0), (start[0] - w, maxY), (end[0] + w, 0), (end[0] + w, maxY)])
        cv2.line(img, cut_points[0][0], cut_points[0][1], (255,), 3)
        cv2.line(img, cut_points[0][2], cut_points[0][3], (255,), 3)
    # average value of the width (margin excluded) of every elements identified
    # on the "1-row array crushed image"
    width = (sum(end) - sum(start))/len(start) + margin
    if col == True:
        return (img, cut_points, width, img_core_col)
    else:
        return (img, cut_points, width)


def get_equations(points):
    """ Calculate affine equations of inputted points
    
    Input : 1
        points : list of list 
            ex : [[[x1, y1], [x2, y2]], [[xx1, yy1], [xx2, yy2]]] for 2 identified
            elements 
            Contains coordinates of separation lines i.e. 
            [[[start points x, y], [end points x, y]] [...], [...]]            
    Output : 2
        columns_a : list of list
            Contains all the a coefficients of an affine equation (y = ax + b)
            of all the calculated lines, in the same order as the input
        columns_b : list of list
            Contains all the b coefficients of an affine equation (y = ax + b)
            of the all the calculated lines, in the same order as the input"""
    columns_a, columns_b = [], []
    # iterate throught points
    for k in points:
        # calculate the a coefficients of start and end separation lines of this element
        a1 = (k[0][1] - k[1][1])/(k[0][0] - k[1][0])
        a2 = (k[2][1] - k[3][1])/(k[2][0] - k[3][0])
        columns_a.append([a1, a2])
        # then calculate the b coefficients of start and end separation lines
        # using the a coeff calculated before
        b1 = k[0][1] - a1*k[0][0]
        b2 = k[2][1] - a2*k[2][0]
        columns_b.append([b1, b2])
    return (columns_a, columns_b)

def line_intersection(startCol_a, endCol_a, startCol_b, endCol_b, startRow_a, endRow_a,
                      startRow_b, endRow_b, aff, y_offset, x_offset):
    '''Is used in "get the rows" part of the class "Cluster Window"
    It gets the insection point of lines (here columns and rows), 
    i.e. the 4 corners of the plot
    Note : we have y = a*x + b for an affine equation
    Note: "start" and "end" refers here to the considered plot here
    Note : the 2 element in every column/row parameters are the line delimiting
        the column/rows when oriented horizontally (separating lines are vertical)
        Element 0 : the first line ("on the left side") 
        Element 1 : the second line ("on the right side")
        When a parameters are considered, the two value are either identical or
        very close.
    
    Inputs : 11
        startCol_a : list of 2 elements
            list of the a parameter for the start column
        endCol_a : list of two elements
            list of the a parameter for the end column
        startCol_b : list of 2 elements
            list of the b parameter for the start column 
        endCol_b : list of 2 elements
            list of the b parameter for the end column
        startRow_a : list of 2 elements
            list of the a parameter for the start row
        endRow_a : list of 2 elements
            list of the a parameter for the end row
        startRow_b : list of 2 elements
            list of the b parameter for the start row
        endRow_b : list of 2 elements
            list of the b parameter for the end row
        aff : Affine object OR int (0)
            Affine transformation matrix associated with the original image
            georeferencement, project the calculated points into its CRS
            Equals zero if the original image is not georeferenced
        - Following inputs are the number of pixels cropped in the very first 
        step of the program (at binarization) to make the running time faster
        y_offset : int
            top pixels
        x_offset :
            left pixels

    Outputs : 1
        [pt4, pt3, pt2, pt1, pt4_geo, pt3_geo, pt2_geo, pt1_geo]
        list of 8 tuple-elements
            corners of the plot, clockwise
            first 4 points are pixels coordinates
            last 4 points are georeferenced (equals 0 if the original image is
            not georeferenced) 
        '''
    # if the a parameter is the same, then there is no crossing points
    # should never happen
    if startCol_a[0] == startRow_a[0]:
        print ("These lines are parallel.")
        return None
    # caculate the common point between the lines
    # x = (b1 - b2) / (a2 - a1)
    # y = a1 * x + b1
    x1 = (startRow_b[0] - startCol_b[0])/(startCol_a[0] - startRow_a[0])
    y1 = (startRow_a[0] * x1 + startRow_b[0])
    x2 = (endRow_b[1] - startCol_b[0])/(startCol_a[1] - endRow_a[0])
    y2 = endRow_a[0] * x2 + endRow_b[1]
    x3 = (endRow_b[1] - endCol_b[1])/(endCol_a[1] - endRow_a[1])
    y3 = endRow_a[1] * x3 + endRow_b[1]
    x4 = (startRow_b[0] - endCol_b[1])/(endCol_a[0] - startRow_a[1])
    y4 = startRow_a[0] * x4 + startRow_b[0]
    # calculate the non-georeferenced coordinates of the plot
    # no affine transformation applied ; -1*y because for images the axis goes down
    pt1 = (x1 + x_offset, - y1 - y_offset)
    pt2 = (x2 + x_offset, - y2 - y_offset)
    pt3 = (x3 + x_offset, - y3 - y_offset)
    pt4 = (x4 + x_offset, - y4 - y_offset)
    # if aff = 0, it means the original image was not georeferenced
    if aff == 0:
        # return the points clock wise 
        return ([pt4, pt3, pt2, pt1], None)
    # if the original is georeferenced, get the coord in the original geotiff
    # system, i.e. multiply by the affine transformation matrix
    else:
        # georeferenced points
        pt1_geo = (x1 + x_offset, y1 + y_offset)*aff
        pt2_geo = (x2 + x_offset, y2 + y_offset)*aff
        pt3_geo = (x3 + x_offset, y3 + y_offset)*aff
        pt4_geo = (x4 + x_offset, y4 + y_offset)*aff
        #return both points
        return ([pt4, pt3, pt2, pt1], [pt4_geo, pt3_geo, pt2_geo, pt1_geo])

def make_shp(folder, nbCol, nbRow, points):
    '''Is used in "get the rows" part of the class "Cluster Window"
    Makes *.shp files according to inputted points in a CLOCKWISE order
    
    Inputs : 4
        folder : path object
            Absolute path to the folder where to save the *.shp
        nbCol : int
            number of the considered column (used in the file names)
        nbRow : int
            number of the considered row (used in the file names)
        points : list of 4 tuple-elements
            points used to define the polygon area
    
    Outputs : none
    '''
    #get the saving name of the file
    save_path = folder / str('Col_' + str(nbCol) + '_row_' + str(nbRow) + '.shp')
    # "close" the shp byt adding the start point at the end
    points.append(points[0])
    # write a new shp file as a polygon shape
    w = shapefile.Writer(str(save_path), shapeType = 5)
    # make the geometry out of the points list
    w.poly([points])
    # fields definition : 
    # column number field
    w.field('Col_nb','N', '40')
    # row number field
    w.field('Row_nb','N', '40')
    # save values into fields
    w.record(int(nbCol), int(nbRow))
    # close the *.shp, thus saving it
    w.close()

def metadata(main_folder, field_image, noise, ColPerPlot, 
             RowPerPlot, orientation, rows_folder, SHP_folder, angle, 
             nbOfColumn, nbOfRowPerColumn, inter, aff, inter_geo):
    ''' Used in the very last part of the class "ClusterWindow" 
    Gather and save the metadata in a txt file.
    
    Inputs : 15
        main_folder : Path object
            absolute path to the whole directory containing all saved files
        field_image : Path object
            absolute path to the original image
        noise : int
            inputted noise removal value
        ColPerPlot : int
            inputted value for "Number of column(s) per plot"
        RowPerPlot : int
            inputted value for "Number of row(s) per plot"
        orientation : str
            checked option in the GUI, either 'H' (horizontal option checked)
            or 'V' (vertical option checked)
        rows_folder : Path object
            absolute path to the folder containing the cropped plot in the
            binary image
        SHP_folder : Path object
            absolute path to the folder containing the *.shp files
        angle : float
            value of the angle needed to rotate the image horizontally (degrees)
        nbOfColumn : int
            number of detected columns in the whole field
        nbOfRowPerColumn : float
            average number of rows per columns
        inter : list of list 
            list of all the corners coordinates of the specified column and row
            NON_GEOREFERENCED, organized as follows : 
            [[Column_nb; Row+nb; pt1_x; pt1_y; pt2_x; pt2_y; pt3_x; pt3_y; pt4_x; pt4_y]]
            Points are displayed clockwise
            ex for the rows "0" and "1" of the column "0" :
                [[0;0;3111.57;-1854.42;2248.22;-1525.92;2673.94;-419.76;3536.17;-751.17;3111.57;-1854.42],
                 [0;1;2247.05;-1526.05;1372.21;-1188.63;1797.99;-82.50;2673.17;-419.03;2247.05;-1526.05]]
        aff : Affine object
            Affine transformation matrix of the original image
            Equals 
            | 1.00, 0.00, 0.00|
            | 0.00, 1.00, 0.00|
            | 0.00, 0.00, 1.00|
            if the original image is not georeferenced.  
        inter_geo : list of list
            list of all the corners coordinates of the specified column and row,
            GEOREFERENCED, organized as follows :
            ex for the rows "0" and "1" of the column "0" :
                [[0;0;3111.57;-1854.42;2248.22;-1525.92;2673.94;-419.76;3536.17;-751.17;3111.57;-1854.42],
                 [0;1;2247.05;-1526.05;1372.21;-1188.63;1797.99;-82.50;2673.17;-419.03;2247.05;-1526.05]]
    
    Outputs : none'''
    # writes the metadata text file
    with open(main_folder / 'metadata.txt', 'w+') as f:
        f.write('##### METADATA #####')
        f.write('\n\n## Inputs')
        f.write('\nWhole field image: ')
        f.write(str(field_image))
        f.write('\nNoise removal (px): ')
        f.write(str(noise))
        f.write('\nNumber of column(s) per plot: ')
        f.write(str(ColPerPlot))
        f.write('\nNumber of row(s) per plots: ')
        f.write(str(RowPerPlot))
        f.write('\nGlobal orientation of the columns: ')
        if orientation == 'H':
            f.write('horizontal')
        else:
            f.write('vertical')
        f.write('\n\n## Files paths')
        f.write('\nMain folder: ')
        f.write(str(main_folder))
        f.write('\nShapefile with all the plots: ')
        f.write(str(main_folder / 'All_plots.shp'))
        f.write('\nBinary plots folder: ')
        f.write(str(rows_folder))
        f.write('\nSHP folder: ')
        f.write(str(SHP_folder))
        f.write('\n\n## Calculated metadata')
        if aff != 0:
            f.write('\nTransform affine matrix:\n')
            f.write(str(aff))
        f.write('\nAngle (compared to an horizontal line): ')
        f.write(str(angle))
        f.write('\nNumber of column(s): ')
        f.write(str(nbOfColumn))
        f.write('\nAverage number of row(s): ')
        f.write(str(nbOfRowPerColumn))
    
    # write the csv file containing the corner coordinates
    csv_file = main_folder / "Intersection_points_non_georeferenced.csv"
    inter = np.array(inter)
    np.savetxt(csv_file, inter, delimiter = ';', newline='\n', header = 'Column;Row;pt1_x;pt1_y;pt2_x;pt2_y;pt3_x;pt3_y;pt4_x;pt4_y', comments = '', fmt='%s')

    if inter_geo != []:
        csv_file = main_folder / "Intersection_points_georeferenced.csv"
        inter = np.array(inter)
        np.savetxt(csv_file, inter_geo, delimiter = ';', newline='\n', header = 'Column;Row;pt1_x;pt1_y;pt2_x;pt2_y;pt3_x;pt3_y;pt4_x;pt4_y', comments = '', fmt='%s')
