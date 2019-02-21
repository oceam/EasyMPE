# -*- coding: utf-8 -*-

"""

2019, L. Tresch for University of Tokyo, Field Phenomics Research Laboratory
Please read the read_me.txt for furter information.

Reverse calculation code is based on Pix4D outputs and Pix4D explanations.

"""

###############################################################################
################################ ENVIRONMENT ##################################
###############################################################################

from pathlib import Path
import cv2, numpy as np, rasterio.transform
from shutil import rmtree
from PyQt5.QtWidgets import (QApplication, QGridLayout, QLabel, QSpinBox, 
        QWidget, QPushButton, QMessageBox, QFileDialog, QComboBox, 
        QRadioButton, QCheckBox)
from PyQt5.QtCore import Qt
from skimage import  morphology
from EasyMPE_plot_identification import MPE
from EasyMPE_revCal import ReverseCalculation

###############################################################################
#################################### CODE #####################################
###############################################################################

class MainWindow(QWidget):
    """ This class contain the GUI and the functions for the Main window \n
    and uses all the other classes."""
    
    def __init__(self):
        super(MainWindow, self).__init__()
        """Overall layout of the main window."""
        self.setWindowTitle('Plot segmentation')
        self.resize(self.sizeHint())
        
        ## initialization
        self.field_image = None
        self.displaySize = 400
        self.noise = 500
        self.DSM = None
        self.offset = None
        self.PMat = None
        self.rawImgFold = None

        ## definition
        self.text_intro = QLabel('Please refer to the read_me.txt if any complication arises.')
        self.text_intro.setAlignment(Qt.AlignCenter)
        self.text_screenSize = QLabel('Select your screen resolution:')
        self.text_screenSize2 = QLabel('\t(if the size is not in the list, please choose a smaller size)')
        self.comboBox_screenSize = QComboBox()
        self.comboBox_screenSize.addItem('1024 x 640 pixels')
        self.comboBox_screenSize.addItem('1280 x 800 pixels')
        self.comboBox_screenSize.addItem('1440 x 900 pixels')
        self.comboBox_screenSize.addItem('1680 x 1050 pixels')        
        self.comboBox_screenSize.addItem('2048 x 1152 pixels')
        self.comboBox_screenSize.addItem('2560 x 1140 pixels')
        self.comboBox_screenSize.addItem('3200 x 1800 pixels')
        self.text_fieldImage = QLabel('Choose the field image: ')
        self.button_fieldImage = QPushButton('Choose')
        self.text_image = QLabel('Image chosen :')
        self.text_imagePath = QLabel(str(self.field_image))
        self.text_imagePath.setAlignment(Qt.AlignCenter)
        self.check_binary = QCheckBox('Binary image')
        self.text_noise = QLabel('Noise removal (px) :')
        self.spinbox_noise = QSpinBox()
        self.spinbox_noise.setRange(1, 10000)
        self.spinbox_noise.setValue(500)
        self.button_drawField = QPushButton('Define the field area')
        
        self.text_plot = QLabel('Plot parameters :')
        self.text_plot.setAlignment(Qt.AlignCenter)
        self.text_nbOfRowPerPlot = QLabel('Number of row(s) per plot:')
        self.spinbox_nbOfRowPerPlot = QSpinBox()
        self.spinbox_nbOfRowPerPlot.setRange(1, 100)
        self.spinbox_nbOfRowPerPlot.setSingleStep(1)
        self.spinbox_nbOfRowPerPlot.setValue(1)
        self.text_nbOfColumnPerPlot = QLabel('Number of column(s) per plot:')
        self.spinbox_nbOfColumnPerPlot = QSpinBox()
        self.spinbox_nbOfColumnPerPlot.setRange(1, 100)
        self.spinbox_nbOfColumnPerPlot.setSingleStep(1)
        self.spinbox_nbOfColumnPerPlot.setValue(1)
        self.text_plotArrangment = QLabel('Global orientation of the columns :')
        self.radio_horizontal = QRadioButton('Horizontal\t\t\t')
        self.radio_horizontal.setChecked(False)
        self.radio_vertical = QRadioButton('Vertical')
        self.radio_vertical.setChecked(False)
        self.button_apply = QPushButton('Apply')

        self.text_intro_revCal = QLabel('If you want to perform reverse calculation :')
        self.text_DSM = QLabel('Digital Surface Model (DSM) :')
        self.button_DSM = QPushButton('Choose')
        self.text_offset = QLabel('Offset :')
        self.button_offset = QPushButton('Choose')
        self.text_PMat = QLabel('PMatrix :')
        self.button_PMat = QPushButton('Choose')
        self.text_rawImgFold = QLabel('Raw images folder :')
        self.button_rawImgFold = QPushButton('Choose')
        self.button_apply_revCal = QPushButton('Apply')
        
        ## connections
        self.button_fieldImage.clicked.connect(self.fieldImage_clicked)
        self.button_drawField.clicked.connect(self.drawField_clicked)
        self.comboBox_screenSize.activated.connect(self.ScreenSizeFunction)
        self.button_apply.clicked.connect(self.application)
        self.button_DSM.clicked.connect(self.button_DSM_clicked)
        self.button_offset.clicked.connect(self.button_offset_clicked)
        self.button_PMat.clicked.connect(self.button_PMat_clicked)
        self.button_rawImgFold.clicked.connect(self.button_rawImgFold_clicked)
        self.button_apply_revCal.clicked.connect(self.button_apply_revCal_clicked)
        
        ## options
        self.button_drawField.hide()
        self.text_imagePath.hide()
        self.text_image.hide()
        self.text_plot.hide()
        self.text_nbOfColumnPerPlot.hide()
        self.spinbox_nbOfColumnPerPlot.hide()
        self.text_nbOfRowPerPlot.hide()
        self.spinbox_nbOfRowPerPlot.hide()
        self.button_apply.hide()
        self.text_plotArrangment.hide()
        self.radio_horizontal.hide()
        self.radio_vertical.hide()
        self.text_intro_revCal.hide()
        self.text_DSM.hide()
        self.button_DSM.hide()
        self.text_offset.hide()
        self.button_offset.hide()
        self.text_PMat.hide()
        self.button_PMat.hide()
        self.text_rawImgFold.hide()
        self.button_rawImgFold.hide()
        self.button_apply_revCal.hide()
        
        ## layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.text_intro, 1, 0, 1, -1)
        self.layout.addWidget(self.text_screenSize, 2, 0)
        self.layout.addWidget(self.comboBox_screenSize, 2, 1)
        self.layout.addWidget(self.text_screenSize2, 2, 2)
        self.layout.addWidget(self.text_fieldImage, 3, 0)
        self.layout.addWidget(self.button_fieldImage, 3, 1, 1, -1)
        self.layout.addWidget(self.text_image, 4, 0)
        self.layout.addWidget(self.text_imagePath, 5, 0, 1, -1)
        self.layout.addWidget(self.text_noise, 6, 0)
        self.layout.addWidget(self.spinbox_noise, 6, 1, 1, -1)
        self.layout.addWidget(self.check_binary, 7, 1)
        self.layout.addWidget(self.button_drawField, 8, 0, 1, -1)
        self.layout.addWidget(self.text_plot, 9, 0)
        self.layout.addWidget(self.text_nbOfColumnPerPlot, 10, 0)
        self.layout.addWidget(self.spinbox_nbOfColumnPerPlot, 10, 1, 1, -1)
        self.layout.addWidget(self.text_nbOfRowPerPlot, 11, 0)
        self.layout.addWidget(self.spinbox_nbOfRowPerPlot, 11, 1, 1, -1)
        self.layout.addWidget(self.text_plotArrangment, 12, 0)
        self.layout.addWidget(self.radio_horizontal, 12, 1)
        self.layout.addWidget(self.radio_vertical, 12, 2)
        self.layout.addWidget(self.button_apply, 13, 0, 1, -1)
        self.layout.addWidget(self.text_intro_revCal, 14, 0, 1, -1)
        self.layout.addWidget(self.text_DSM, 15, 0)
        self.layout.addWidget(self.button_DSM, 15, 1, 1, -1)
        self.layout.addWidget(self.text_offset, 16, 0)
        self.layout.addWidget(self.button_offset, 16, 1, 1, -1)
        self.layout.addWidget(self.text_PMat, 17, 0)
        self.layout.addWidget(self.button_PMat, 17, 1, 1, -1)
        self.layout.addWidget(self.text_rawImgFold, 18, 0)
        self.layout.addWidget(self.button_rawImgFold, 18, 1, 1, -1)
        self.layout.addWidget(self.button_apply_revCal, 19, 0, 1, -1)
        self.setLayout(self.layout)  
        
        self.show()


    def ScreenSizeFunction(self):
        """ This function is part of the class 'MainWindow'. \n
        It is linked to the change of the combo box self.comboBox_screenSize \n
        It decides the maximum size for the display of pictures depending on the
        inputted size of the screen """
        if self.comboBox_screenSize.currentText() == '1024 x 640 pixels':
            self.displaySize = 400
        if self.comboBox_screenSize.currentText() == '1280 x 800 pixels':
            self.displaySize = 600
        if self.comboBox_screenSize.currentText() == '1440 x 900 pixels':
            self.displaySize = 700
        if self.comboBox_screenSize.currentText() == '1680 x 1050 pixels':
            self.displaySize = 800
        if self.comboBox_screenSize.currentText() == '2048 x 1152 pixels':
            self.displaySize = 900
        if self.comboBox_screenSize.currentText() == '2560 x 1140 pixels':
            self.displaySize = 900
        if self.comboBox_screenSize.currentText() == '3200 x 1800 pixels':
            self.displaySize = 1600

    def fieldImage_clicked(self):
        """ This function is part of the class 'MainWindow' \n
        It is connected to the button button_fieldImage and allows the user to
        chose the image of the whole field on which all the program is based"""
        self.field_image, _ = QFileDialog.getOpenFileName(self, "Select the field image", "",".tif or .tiff or .jpg or .jpeg or .png (*.tif *.tiff *.TIF *.TIFF *.jpg *.jpeg *.JPG *.JPEG *.PNG *.png)", options=QFileDialog.DontUseNativeDialog)
        self.field_image = Path(self.field_image)
        self.text_imagePath.setText(str(self.field_image))
        if self.field_image.is_file():
            self.button_drawField.show()
            self.text_imagePath.show()
            self.text_image.show()
        else:
            self.button_drawField.hide()
            self.text_imagePath.hide()
            self.text_image.hide()
        self.coord = []
        self.text_plot.hide()
        self.text_nbOfRowPerPlot.hide()
        self.spinbox_nbOfRowPerPlot.hide()
        self.text_nbOfColumnPerPlot.hide()
        self.spinbox_nbOfColumnPerPlot.hide()
        self.button_apply.hide()
        self.text_plotArrangment.hide()
        self.radio_horizontal.hide()
        self.radio_vertical.hide()
        self.text_intro_revCal.hide()
        self.text_DSM.hide()
        self.button_DSM.hide()
        self.text_offset.hide()
        self.button_offset.hide()
        self.text_PMat.hide()
        self.button_PMat.hide()
        self.text_rawImgFold.hide()
        self.button_rawImgFold.hide()
        self.button_apply_revCal.hide()

    def drawField_clicked(self):
        """This function is part of the class 'MainWindow' \n
        It is connected to the button button_drawField and opens the beforehand
        chosen image of fieldImage_clicked into a new window so the user can
        select the field points as they wish. The image is then binarized using
        ExGreen calculation and cropped to avoid useless data storage"""
        
        # instructions
        QMessageBox.about(self, 'Information', "A drawing window will appear. \nTo quit without saving, press E.\nTo re-start, press Q. \nWhen you are finished, press O. \n\nPlease indicate the corners of the field.")
        
        # initialization
        self.coord = []
        self.img = cv2.imread(str(self.field_image))
        img_name = self.field_image.stem
        WindowsName = 'Select 4 corner points'
        self.YN_binary = self.check_binary.isChecked()
        self.noise = self.spinbox_noise.value()
 
        # make a repertory
        self.main_folder = self.field_image.parent / str('Micro_plots_' + img_name)
        if self.main_folder.is_dir():
            rmtree(self.main_folder, ignore_errors = True)
        try:
            self.main_folder.mkdir()   
        except PermissionError:
            QMessageBox.about(self, 'Information', "A previous image folder existed and opened. It has been erased.")
            self.main_folder.mkdir()   
        except FileExistsError:
            QMessageBox.about(self, 'Information', "A file of the previous folder is opened. Please close it and re-try. The previous file will be deleted, please change its name or emplacement if you wish to keep it.")
            return
        
        #resize the image according to the screen size 
        if len(self.img[:, 0]) >= len(self.img[0,:]) : #if the picture's height is bigger than its width 
            H = self.displaySize
            coeff = H/len(self.img[:, 0])
            W = int(coeff*len(self.img[0, :]))
        else: # if width is bigger than height
            W = self.displaySize
            coeff = W/len(self.img[0, :])
            H = int(coeff*len(self.img[:, 0]))
        self.img = cv2.resize(self.img, (W, H)) 

        # display the picture in a new window
        cv2.namedWindow(WindowsName) 
        cv2.setMouseCallback(WindowsName, self.draw_point, param = None)
        
        # events while drawing (infinite loop)
        while (1):
            # show the image window
            cv2.imshow(WindowsName, self.img)
            key = cv2.waitKey(20) & 0xFF
            
            # to restart the drawing
            if key == ord('q'): 
                # reload the original image (without any points on it)
                self.img = cv2.imread(str(self.field_image))
                self.img = cv2.resize(self.img, (W, H)) 
                cv2.namedWindow(WindowsName, cv2.WINDOW_NORMAL) # define the name of the window again
                cv2.setMouseCallback(WindowsName, self.draw_point, param = None) # call the function 
                self.coord = [] # do not save any coordinates

            # to exit and stop the drawing mode
            if key == ord('e'):
                self.coord = [] # no pixels are saved
                QMessageBox.about(self, 'Information', "No pixels are selected.")
                # close the window and make sure the GUI only shows usable
                # buttons at this stage
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                self.text_plot.hide()
                self.text_nbOfRowPerPlot.hide()
                self.spinbox_nbOfRowPerPlot.hide()
                self.text_nbOfColumnPerPlot.hide()
                self.spinbox_nbOfColumnPerPlot.hide()
                self.button_apply.hide()
                self.text_plotArrangment.hide()
                self.radio_horizontal.hide()
                self.radio_vertical.hide()
                self.text_intro_revCal.hide()
                self.text_DSM.hide()
                self.button_DSM.hide()
                self.text_offset.hide()
                self.button_offset.hide()
                self.text_PMat.hide()
                self.button_PMat.hide()
                self.text_rawImgFold.hide()
                self.button_rawImgFold.hide()
                self.button_apply_revCal.hide()
                return
            
            # to finish the drawing and save the points drawn
            if key == ord('o'): 
                # field must be at least rectangular
                if len(self.coord) < 3:
                    QMessageBox.about(self, 'Information', "Please select at least 3 points. \nIf you want to escape, press 'e' key.")
                else: 
                    ## when done, saving the images and producing exG + binary images
                    # close the drawing with the last magenta line
                    cv2.line(self.img, self.coord[-1], self.coord[0], (255, 0, 255), 1)
                    cv2.imshow(WindowsName, self.img)
                    QMessageBox.about(self, 'Information', "Selected pixels are : \n" + str(self.coord) + '\n\nThe image will be processed. Please wait a few seconds.')
                    # save the coordinate image
                    cv2.imwrite(str(self.main_folder / 'Field_points.jpg'), self.img)
                    cv2.destroyWindow(WindowsName)
                    
                    self.img = get_drawn_image(self.field_image, self.coord, coeff)
                    # if the image is not binary i.e. has more than 1 channel
                    if self.YN_binary == False:
                        # get coordinates of the first non-black pixels
                        coords = np.argwhere(self.img)
                        try:
                            y0, x0, z = coords.min(axis = 0)
                            y1, x1, z = coords.max(axis = 0) + 1
                            # generate a binary image
                            self.img_exG, self.img_binary = get_binary(self.img, self.noise)
                            # cut all images according to avoid useless black pixels
                            self.img = self.img[y0:y1, x0:x1]
                            self.img_exG = self.img_exG[y0:y1, x0:x1]
                            self.img_binary = self.img_binary[y0:y1, x0:x1]
                            # save outputs
                            cv2.imwrite(str(self.main_folder / 'ExcessGreen.tiff'), self.img_exG)
                            cv2.imwrite(str(self.main_folder / 'Field_area.tiff'), self.img)
                        except ValueError:
                            QMessageBox.about(self, 'Information', "It seems that your image is a binary. It will be considered as binary for the rest of the program.")
                            self.YN_binary == True
                            y0, x0 = coords.min(axis = 0)
                            y1, x1 = coords.max(axis = 0) + 1
                            self.img = self.img[y0:y1, x0:x1]
                            # apply the noise removal
                            B = (self.img != 0)
                            self.img_binary = morphology.remove_small_objects(B, min_size = int(self.noise))*255
                    else:
                        # get rid of the useless black pixels
                        coords = np.argwhere(self.img)
                        y0, x0 = coords.min(axis = 0)
                        y1, x1 = coords.max(axis = 0) + 1
                        self.img = self.img[y0:y1, x0:x1]
                        # apply the noise removal
                        B = (self.img != 0)
                        self.img_binary = morphology.remove_small_objects(B, min_size = int(self.noise))*255
                    # save binary image
                    cv2.imwrite(str(self.main_folder / 'Binary_image.tiff'), self.img_binary)
                    
                    # displays buttons useful for next steps
                    self.text_plot.show()
                    self.text_nbOfRowPerPlot.show()
                    self.spinbox_nbOfRowPerPlot.show()
                    self.text_nbOfColumnPerPlot.show()
                    self.spinbox_nbOfColumnPerPlot.show()
                    self.button_apply.show()
                    self.text_plotArrangment.show()
                    self.radio_horizontal.show()
                    self.radio_vertical.show()
                    self.text_intro_revCal.hide()
                    self.text_DSM.hide()
                    self.button_DSM.hide()
                    self.text_offset.hide()
                    self.button_offset.hide()
                    self.text_PMat.hide()
                    self.button_PMat.hide()
                    self.text_rawImgFold.hide()
                    self.button_rawImgFold.hide()
                    self.button_apply_revCal.hide()
                    # save the value of cutted black parts for the end of the 
                    # program (shp files)
                    self.y_offset, self.x_offset = y0, x0
                    break
            
    def draw_point (self, event, x, y, flags, param):
        """ This function is part of the class 'MainWindow' and is used in the
        function 'drawField_clicked'. 
        It draws a red circle everytime the right
        button of the mouse is clicked down. If there is more than one point, a 
        magenta line will link the two latest points clicked.
        
        Inputs : 5
            event : mouth clicked down
            x : position on the x-axis
            y : position on the y-axis (going down)
            flags : 
            param : None [could pass a specific color if needed]
            """
        if event == cv2.EVENT_LBUTTONDOWN: 
            #when the button is pushed, the first pixel is recorded and a circle is drawn on the picture
            self.coord.append((int(x), int(y)))
            cv2.circle(self.img, (x,y), 6, (0, 0, 255), -1) #draw the circle
            if len(self.coord) > 1:
                cv2.line(self.img, self.coord[-2], self.coord[-1], (255, 0, 255), 1)
                
    def application(self):
        """ This function is part of the class 'MainWindow'.
        It is linked to the button 'button_apply' and starts the image 
        processing (i.e. clustering, cropping, *.shp files, reverse calculation) 
        """
        if self.radio_horizontal.isChecked() == False and self.radio_vertical.isChecked() == False:
            QMessageBox.about(self, 'Information', "Please indicate if the columns are displayed more vertically or horizontally oriented. \nIf no particular orientation stands out, choose one randomly.")
        else:
            img_raster = rasterio.open(self.field_image)
            aff = img_raster.transform
            self.crs = img_raster.crs
            if type(self.crs) == type(None):
                aff = 0
            img_raster.close()
            nbRow = self.spinbox_nbOfRowPerPlot.value()
            nbColumn = self.spinbox_nbOfColumnPerPlot.value()
            if self.radio_horizontal.isChecked() == True:
                orientation = 'H'
            elif self.radio_vertical.isChecked() == True:
                orientation = 'V'
            # inform the user the program is finished

            output = MPE(self.img_binary, self.main_folder, self.img, self.YN_binary,
                nbRow, nbColumn, orientation, self.noise,
                self.field_image, aff, self.y_offset, self.x_offset)
        
            if output == '1':
                QMessageBox.about(self, 'Information', 'Sorry, no column has been detected. Please change the input parameters and retry.')
                self.text_intro_revCal.hide()
                self.text_DSM.hide()
                self.button_DSM.hide()
                self.text_offset.hide()
                self.button_offset.hide()
                self.text_PMat.hide()
                self.button_PMat.hide()
                self.text_rawImgFold.hide()
                self.button_rawImgFold.hide()
                self.button_apply_revCal.hide()
            if output == '2':
                QMessageBox.about(self, 'Information', 'Sorry, no rows has been detected. Please change the input parameters and retry.')
                self.text_intro_revCal.hide()
                self.text_DSM.hide()
                self.button_DSM.hide()
                self.text_offset.hide()
                self.button_offset.hide()
                self.text_PMat.hide()
                self.button_PMat.hide()
                self.text_rawImgFold.hide()
                self.button_rawImgFold.hide()
                self.button_apply_revCal.hide()
            elif output == 'OK' :
                QMessageBox.about(self, 'Information', '''Micro-plot extraction finished !''')
                # if the original image is georeferenced
                if type(self.crs) != type(None):
                    # unlock inputs for reverse calculation
                    self.text_intro_revCal.show()
                    self.text_DSM.show()
                    self.button_DSM.show()
                    self.text_offset.show()
                    self.button_offset.show()
                    self.text_PMat.show()
                    self.button_PMat.show()
                    self.text_rawImgFold.show()
                    self.button_rawImgFold.show()
                    self.button_apply_revCal.show()
                else :
                    QMessageBox.about(self, 'Information', 'The original image is not georeferenced. Thus, reverse calculation cannot be proposed.')
                # make sure everything is unchecked/back to the original value
                self.spinbox_nbOfRowPerPlot.setValue(1)
                self.spinbox_nbOfColumnPerPlot.setValue(1)
                self.radio_horizontal.setChecked(False)
                self.radio_vertical.setChecked(False)

    def button_DSM_clicked(self):
        self.DSM, _ = QFileDialog.getOpenFileName(self, "Select the DSM file", "",".tif or .tiff (*.tif *.tiff *.TIF *.TIFF)", options=QFileDialog.DontUseNativeDialog)
        self.DSM = Path(self.DSM)
    
    def button_offset_clicked(self):
        self.offset, _ = QFileDialog.getOpenFileName(self, "Select the offset file", "",".xyz or .txt (*.txt *.xyz)", options=QFileDialog.DontUseNativeDialog)
        self.offset = Path(self.offset)
        
    def button_PMat_clicked(self):
        self.PMat, _ = QFileDialog.getOpenFileName(self, "Select the PMatrix file", "",".txt (*.txt)", options=QFileDialog.DontUseNativeDialog)
        self.Pmat = Path(self.PMat)
        
    def button_rawImgFold_clicked(self):
        self.rawImgFold = QFileDialog.getExistingDirectory(self, "Select the drone images folder")
        self.rawImgFold = Path(self.rawImgFold)

    def button_apply_revCal_clicked(self):
        if self.DSM is None or self.offset is None or self.PMat is None or self.rawImgFold is None:
            QMessageBox.about(self, 'Error', 'There are missing files. Please make sure you provided all the inputs.')
        else :

            revCal_csv = ReverseCalculation(self.main_folder, self.DSM, self.offset, self.PMat, 
                                     self.rawImgFold)
                        
            QMessageBox.about(self, 'Information', 'Reverse calculation finished ! Output at : ' + 
                              str(revCal_csv))
            self.DSM = None
            self.offset = None
            self.PMat = None
            self.rawImgFold = None
                        
###############################################################################
################################## FUNCTIONS ##################################
###############################################################################

def get_drawn_image(image, coord, coeff):
    """ Used in class 'MainWindow' in function 'drawField_clicked' 
    Make a mask out of inputted coordinates and apply it on the image
    
    Inputs : 3
        image : list of list
            the field image on which points were drawn
        coord : list
            the selected points coordinates
        coeff : int
            the coefficient used to resize the image for it to fit the 
            screen resolution
                
    Output : 1
        masked_image : list of list 
            cut out image according to the inputted points
        """
    img = cv2.imread(str(image), -1)
    # init
    mask = np.zeros(img.shape, dtype = np.uint8)
    roi_corners = []
    # get the right synthax for the array
    for k in coord:
        roi_corners.append((int(k[0]/coeff), int(k[1]/coeff)))
    roi_corners = np.array([roi_corners], dtype = np.int32)
    # get the region to keep
    try:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
    except IndexError:
        channel_count = 1
    ignore_mask_color = (255,)*channel_count
    cv2.fillPoly(mask, roi_corners, ignore_mask_color)
    # apply the mask
    masked_image = cv2.bitwise_and(img, mask)  
    return masked_image

def get_binary(img, noise):
    """ Make a binarization of a RGB image using the ExGreen index and remove
    noise as indicated.
    
    Inputs : 2
        img : list of list
            image to binarize, already read
        noise : int
            smaller blobs than this int will be removed
    
    Outputs : 2
        exG : list of list
            excess green index of the original image
        binary : list of list
            binary version of the original image, based on ExG index                
    """
    # get all the channels
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    # calculate the excess green image
    exG = 2*g - r - b
    
    # Floodfill from point (0, 0) aka get black background
    h, w = exG.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(exG, mask, (0,0), 255)
    
    ## apply Otsu threshold
    blur = cv2.GaussianBlur(exG, (3, 3), 0)
    threshold, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # get the negative image (plant in white)
    binary = 255 - binary
    
    # remove noise
    B = (binary != 0)
    B = morphology.remove_small_objects(B, min_size = int(noise))
    binary [B == False] = 0
    return(exG, binary)

###############################################################################
##################################### MAIN ####################################
###############################################################################

if __name__ == '__main__':
    
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())