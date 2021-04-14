#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------------------
# Name  : Image Patches Generator Script
# Date  : April 13, 2021
# Author: Jose L. Agraz, PhD
#
# Description: This program is based on Open Slide Patch Manger (OPM) and 
#              slices an image into patches.  
#              The generated patches properties are defined in a yamel file. 
#              In addition, tow csv files are generated, the first listings
#              patch files names and XY coordinates. The second parses only
#              xy coordinates. The later csv file is meant to be used as an 
#              input to other OPM executions ensuring exact xy patch 
#              coordinates are applied to other images.
#              Added discrete error checking, stdout and stderr datalogger,
#              verbose comments, summary report, and improved variable names
#              
# Usage Example:
#       python patch_miner.py\
#             --Input_Image_Path               /media/jlagraz/MyBookWD/InputImages/TCGA-32-2494-01A-01-TS1.24dfccf0-f73c-4926-833c-059d934bc72f_overlay.tiff
#             --Configuration_Yaml_File        /home/jlagraz/Documents/Normalization/BaSSaN-Update/OpmTiling/ConfigutationFiles/overlap_0.yml
#             --Patches_Output_Path            /media/jlagraz/MyBookWD/Results
#             --Input_XY_Coordinates_Csv_File  /media/jlagraz/MyBookWD/Result/XYPatchCoordinates.csv  
#
#------------------------------------------------------------------------------------------------
import sys
import yaml
import logging
import argparse
import warnings
import functools
import openslide
import numpy  as np
import pandas as pd
#
from pathlib           import Path
from PIL               import Image
from functools         import partial
from datetime          import datetime
from opm.patch_manager import PatchManager
from opm.utils         import tissue_mask, alpha_channel_check, patch_size_check
#
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore")

__author__  = 'Jose L. Agraz, PhD'
__status__  = 'Prototype'
__email__   = 'jose@agraz.email'
__credits__ = ['Sarthak Pati','Siddhesh Thakur','Caleb Grenko','Spyros Bakas, PhD']
__license__ = "GPL"
__version__ = "1.0"
# Global variables
X_DIMENSION          = 0
Y_DIMENSION          = 1
#-----------------------------------------------------------------
# Name: Defining logger
# Author: Jose L. Agraz, PhD
# Date: 06/12/2020
# Description: Logger definitions including decorator
#       https://dev.to/mandrewcito/a-tiny-python-log-decorator-1o5m
#-----------------------------------------------------------------
FORMATTER            = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
LEVEL_NAME           = logging.getLevelName('DEBUG')
DESCRITPTION_MESSAGE = \
                        'This program is based on Open Slide Patch Manger (OPM) and   ' + '\n'\
                        'slices an image into patches.                                ' + '\n'\
                        'The generated patches properties are defined in a yamel file.' + '\n'\
                        'In addition, tow csv files are generated, the first listings ' + '\n'\
                        'patch files names and XY coordinates. The second parses only ' + '\n'\
                        'xy coordinates. The later csv file is meant to be used as an ' + '\n'\
                        'input to other OPM executions ensuring exact xy patch        ' + '\n'\
                        'coordinates are applied to other images.                     ' + '\n'\
                        'Added discrete error checking, stdout and stderr datalogger, ' + '\n'\
                        'verbose comments, summary report, and improved variable names'
#-----------------------------------------------------------------
# Name: Logger Definitions
# Author: Jose L. Agraz, PhD
# Date: 06/12/2020
# Description:
# Input:
# Output:
#-----------------------------------------------------------------
def GetConsoleHandler(TargetOutput):
    # Create console handler and set level to debug
    ConsoleHandler = logging.StreamHandler(TargetOutput)
    # add formatter to Console Logger
    ConsoleHandler.setFormatter(FORMATTER)
    return ConsoleHandler
#-----------------------------------------------------------------
def GetLogger(LoggerName,TargetOutput):
   logger     = logging.getLogger(LoggerName)
   logger.setLevel(LEVEL_NAME) # better to have too much log than not enough
   LogHandler = GetConsoleHandler(TargetOutput)
   logger.addHandler(LogHandler)
   # with this pattern, it's rarely necessary to propagate the error up to parent
   logger.propagate = False
   return logger,LogHandler
#-----------------------------------------------------------------
class LogDecorator(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            try:
                self.logger.info("{0} - {1} - {2}".format(fn.__name__, args, kwargs))
                result = fn(*args, **kwargs)
                self.logger.info(result)
                return result
            except Exception as ex:
                self.logger.debug("Exception!!!! {0}".format(ex), exc_info=True)
                raise ex
            return result
        return decorated
#------------------------------------------------------------------------------------------------
# Function Name: Get Arguments
# Author: Jose L. Agraz, PhD
# Date: 03/12/2020
# Description: Define input arguments using flags
# Input: input image path, Configuration Yaml File, Patches Output Path,Input XY Coordinates CSV File
# Output: Argument list
#------------------------------------------------------------------------------------------------
def GetArguments():
    parser = argparse.ArgumentParser(description=DESCRITPTION_MESSAGE)
    parser.add_argument('-i',    '--Input_Image_Path',              required=True,  help='Image to path to slice')
    parser.add_argument('-c',    '--Configuration_Yaml_File',       required=True,  help='config.yml for running OPM')
    parser.add_argument('-o',    '--Patches_Output_Path',           required=False, help='output path for the patches')
    parser.add_argument('-icsv', '--Input_XY_Coordinates_Csv_File', required=False, help='CSV with x,y coordinates of patches to mine')

    args = parser.parse_args()

    return args   
#------------------------------------------------------------------------------------------------
# Function Name: get folder size
# Author: Jose L. Agraz, PhD
# Date: 03/12/2020
# Description: Calculates directory size in GB
# Input: Directory
# Output: Directory size and number of patches in the directory
# https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
#------------------------------------------------------------------------------------------------
def get_folder_size(folder):
    Gigabytes       = 1024**3
    TotalSum        = sum(file.stat().st_size for file in Path(folder).rglob('*'))
    SumGB           = TotalSum / Gigabytes
    FolderSize      = '{0:.3f}GB'.format(SumGB)
    NumberOfPatches = len(list(Path(folder).rglob('*')))
    return FolderSize,NumberOfPatches
#------------------------------------------------------------------------------------------------
# Function Name: Terminate
# Author: Jose L. Agraz, PhD 
# Date: 04/14/2020
# Description: Summarizes run
# Input: Yaml configuration file details and OPM manage object
# Output: None
#------------------------------------------------------------------------------------------------
def Terminate(ConfigurationFile,manager):
    global InputArguments
    
    RootDirectory              = str(Path(InputArguments.Patches_Output_Path) /manager.slide_folder)
    FolderSize,NumberOfPatches = get_folder_size(RootDirectory)
    
    StdOutLogger.info('----------------------------------------------------')
    StdOutLogger.info('Summary                                             ')
    StdOutLogger.info('----------------------------------------------------')
    StdOutLogger.info('Image Name                : {}   '.format(Path(manager.path).name))
    StdOutLogger.info('Patches Total Size        : {}   '.format(FolderSize))
    StdOutLogger.info('Number of Patches         : {}   '.format(NumberOfPatches))
    StdOutLogger.info('Patches Directory         : {}   '.format(manager.slide_folder))
    StdOutLogger.info('Patch Size                : {}x{}'.format(ConfigurationFile['patch_size'][X_DIMENSION],ConfigurationFile['patch_size'][Y_DIMENSION])) 
    StdOutLogger.info('Patch Saved               : {}   '.format(ConfigurationFile['save_patches'])) 
    StdOutLogger.info('Patching Type             : {}   '.format(ConfigurationFile['read_type']))
    StdOutLogger.info('Patch White Color         : {}   '.format(ConfigurationFile['white_color']))
    StdOutLogger.info('Patch Scale               : {}   '.format(ConfigurationFile['scale']))
    StdOutLogger.info('Overlap Factor            : {}   '.format(ConfigurationFile['overlap_factor']))    
    StdOutLogger.info('Config YML File Name      : {}   '.format(Path(InputArguments.Configuration_Yaml_File).name))
    StdOutLogger.info('Output Directory          : {}   '.format(InputArguments.Patches_Output_Path))    
    StdOutLogger.info('----------------------------------------------------')
# ------------------------------------------------------------------------------------------------
# Function Name: Close Handles
# Author: Jose L. Agraz, PhD
# Date: 04/12/2020
# Description: Closes logger handle
# Input: none
# Output: none
# ------------------------------------------------------------------------------------------------
def CloseHandles():
    StdOutLogger.info('Closing Log handles')
    StdOutLogger.info('Close stream handle')
    LogHandler.close()
    StdOutLogger.info('Remove stream handle from logger')
    StdOutLogger.removeHandler(LogHandler)
    StdOutLogger.info('Shutdown logger upon app exit')
    logging.shutdown()   
#------------------------------------------------------------------------------------------------
# Function Name: Creates a directory
# Author: Jose L. Agraz, PhD
# Date: 04/12/2020
# Description: Created a directory
# Input: path
# Output: none
#------------------------------------------------------------------------------------------------
def CreateDirectory(OutputPath):
    try:
        StdOutLogger.info('Creating directory:\n{}'.format(OutputPath))
        Path(OutputPath).mkdir(parents=True, exist_ok=True)
    except:
        StdOutLogger.info('Could not created directory:\n{}'.format(OutputPath))
        raise IOError()

#------------------------------------------------------------------------------------------------
# Function Name: Initialize
# Author: Jose L. Agraz, PhD 
# Date: 04/14/2020
# Description: Sets up run
# Input: None
# Output: Patches directory and Yaml configuration file details
#------------------------------------------------------------------------------------------------
def Initialize():
    global InputArguments
    
    StdOutLogger.info('Define Input Arguments')
    InputArguments  = GetArguments()
    
    if not Path(InputArguments.Input_Image_Path).exists():
        raise IOError('Could not find the image:\n{}'.format(InputArguments.Patches_Output_Path))
    if not Path(InputArguments.Configuration_Yaml_File).exists():
        raise IOError('Could not find the config file:\n{}'.format(InputArguments.Configuration_Yaml_File))     
    
    if InputArguments.Patches_Output_Path is None:
        PatchesOutputDirectory = ""
    else:
        CreateDirectory(InputArguments.Patches_Output_Path)
        PatchesOutputDirectory = '{}/'.format(Path(InputArguments.Patches_Output_Path)) 
        
    try:        
        StdOutLogger.info('Load config file')
        ConfigurationFile      = yaml.load(open(InputArguments.Configuration_Yaml_File), Loader=yaml.FullLoader)
    except:
        raise IOError('Exception Yaml Load failed')  
        
    return PatchesOutputDirectory,ConfigurationFile
#------------------------------------------------------------------------------------------------
# Function Name: Parse Image List
# Author: Jose L. Agraz, PhD 
# Date: 04/14/2020
# Description: Fetch image list
# Input: File name
# Output: List
#------------------------------------------------------------------------------------------------      
def ParseImageList(ListFileName):
    global InputArguments
    
    ImagesPathsList = list()
    
    StdOutLogger.info('Opening image list: {} '.format(Path(ListFileName).name))
    try:
        # Pandas assumes CSV file has column titles
        ImagesPathsList  = pd.read_csv(ListFileName).squeeze().tolist()
    except:
        raise IOError('Exception triggered!!!')
        
    return ImagesPathsList        
#------------------------------------------------------------------------------------------------
# Function Name: Parse CSV Patches Files
# Author: Jose L. Agraz, PhD
# Date: 04/12/2020
# Description: Parses file names listed in CSV file
# Input: File path and File Name
# Output: XY Coordinates File List
#------------------------------------------------------------------------------------------------
def ParseCsvPatchesFiles(FilePath,FileName):
    global InputArguments
    
    XYCoordinatesDataframe       = pd.DataFrame()
    OutputXYCoordinatesFileList  = list()
    FilePathColumnName           = 'Csv_File_Path'
    X_CoordinateColumnName       = 'X'
    Y_CoordinateColumnName       = 'Y'
    DataframeColumnNames         = [FilePathColumnName,X_CoordinateColumnName,Y_CoordinateColumnName]
    
    StdOutLogger.info('****************************************')
          
    StdOutLogger.info('Reading CSV File: {}'.format(Path(FilePath).stem))
    XYCoordinatesDataframe         = pd.read_csv(FilePath)
    
    StdOutLogger.info('Reset Dataframe Index')
    XYCoordinatesDataframe.reset_index(inplace = True)
    StdOutLogger.info('Rename Columns')
    XYCoordinatesDataframe.columns = DataframeColumnNames
    CleanedXYCoordinatesDataframe  = XYCoordinatesDataframe[[X_CoordinateColumnName,Y_CoordinateColumnName]]
    
    RootCsvFilePath                = str(Path(InputArguments.Patches_Output_Path))
    CreateDirectory(RootCsvFilePath)
    OutputFileName                 = str(Path(FileName).stem) + '_ParsedXY.csv'
    CsvFilePath                    = Path(RootCsvFilePath) / OutputFileName
    StdOutLogger.info('Save Cleaned CSV Patch coordinates file: {}'.format(OutputFileName))
    
    try:
        OutputXYCoordinatesFileList.append(CsvFilePath)
                                    
        if CsvFilePath.is_file():
            StdOutLogger.info('File {} already exist, deleting...'.format(CsvFilePath.name))
            CsvFilePath.unlink()
        
        CleanedXYCoordinatesDataframe.to_csv(str(CsvFilePath), index=False)
    except:
        raise IOError('Can not save CSV file: {}'.format(OutputFileName))
             
    return OutputXYCoordinatesFileList   

#------------------------------------------------------------------------------------------------
# Function Name: Process Patches
# Author: Jose L. Agraz, PhD
# Date: 04/12/2020
# Description: Performs patching
# Input: Patches directory and Yaml configuration file details
# Output: Patch manager object
#------------------------------------------------------------------------------------------------     
def ProcessPatches(PatchesOutputDirectory,ConfigurationFile):
        
    try:
        StdOutLogger.info('Create new instance of slide manager')
        manager           = PatchManager(InputArguments.Input_Image_Path)
    except:
        raise IOError('Exception PatchManager failed')        
     
    if InputArguments.Input_XY_Coordinates_Csv_File is None:
        StdOutLogger.info('User did not provide xy coordinate file, create xy coordinates')
        #-----------------------------------------------------------------
        try:
            StdOutLogger.info('Generate an initial mask')
            mask, scale      = generate_initial_mask(InputArguments.Input_Image_Path,\
                                                     ConfigurationFile['scale'])
        except:
            raise IOError('Exception generate_initial_mask failed')                       
        #-----------------------------------------------------------------
        try:                
            StdOutLogger.info('Generate validity mask')                        
            manager.set_valid_mask(mask, scale)
        except:
            raise IOError('Exception generate_initial_mask failed')
        #-----------------------------------------------------------------
        try:                        
            StdOutLogger.info('Reject patch if any pixels are transparent')
            manager.add_patch_criteria(alpha_channel_check)
        except:
            raise IOError('Exception add_patch_criteria failed')
        #-----------------------------------------------------------------
        try:
            StdOutLogger.info('Reject patch if image dimensions are not equal to {}x{}'.format(ConfigurationFile['patch_size'][X_DIMENSION],\
                                                                                               ConfigurationFile['patch_size'][Y_DIMENSION]))
            patch_dims_check = partial(patch_size_check,\
                                       patch_height = ConfigurationFile['patch_size'][X_DIMENSION],\
                                       patch_width  = ConfigurationFile['patch_size'][Y_DIMENSION])
        except:
            raise IOError('Exception partial failed')                    
        #-----------------------------------------------------------------
        try:
            StdOutLogger.info('Apply Patch Dimesion check')
            manager.add_patch_criteria(patch_dims_check)
        except:
            raise IOError('Exception add_patch_criteria failed')         
            
        #-----------------------------------------------------------------        
        FileName         = str(Path(InputArguments.Input_Image_Path).stem) + 'XYPatchCoordinates.csv'           
        StdOutLogger.info('File Name: {}'.format(FileName))
        StdOutLogger.info('Path Name: {}'.format(InputArguments.Patches_Output_Path))
        OutputCsvFile    = Path(InputArguments.Patches_Output_Path) / FileName
                
        if OutputCsvFile.is_file():
            StdOutLogger.info('File {} already exist, deleting...'.format(FileName))
            OutputCsvFile.unlink()
        # Typecast from Path to string
        OutputCsvFile = str(OutputCsvFile)
            
        #-----------------------------------------------------------------
        try:
            StdOutLogger.info('Save patches releases saves all patches stored in manager, dumps to specified output file')                        
            manager.mine_patches(PatchesOutputDirectory,\
                                 output_csv = OutputCsvFile,\
                                 config     = ConfigurationFile)      
        except:
            raise IOError('Exception mine_patches failed')          

        try:
            StdOutLogger.info('Parse patch coordinates file list')
            ParseCsvPatchesFiles(OutputCsvFile,FileName)
        except:
            raise IOError('Exception parsing csv file failed')                         
    else:
        #-----------------------------------------------------------------
        StdOutLogger.info('User provided xy coordinate file')
        try:
            StdOutLogger.info('XY Coordinate File Name: {}'.format(Path(InputArguments.Input_XY_Coordinates_Csv_File).name))
            StdOutLogger.info('Save predefined patches')
            manager.save_predefined_patches(PatchesOutputDirectory, patch_coord_csv=InputArguments.Input_XY_Coordinates_Csv_File, config=ConfigurationFile)
        except:
            raise IOError('Exception save_predefined_patches failed')   
            
    return manager
#-----------------------------------------------------------------    
def generate_initial_mask(slide_path, scale):
    """
    Helper method to generate random coordinates within a slide
    :param slide_path: Path to slide (str)
    :param num_patches: Number of patches you want to generate
    :return: list of n (x,y) coordinates
    """
    StdOutLogger.info('Open slide and get properties')
    slide           = openslide.open_slide(slide_path)
    slide_dims      = slide.dimensions

    StdOutLogger.info('Call thumbnail for effiency, calculate scale relative to whole slide')
    slide_thumbnail = np.asarray(slide.get_thumbnail((slide_dims[0] // scale, slide_dims[1] // scale)))
    real_scale      = (slide_dims[0] / slide_thumbnail.shape[1], slide_dims[1] / slide_thumbnail.shape[0])

    return tissue_mask(slide_thumbnail), real_scale
               
#-----------------------------------------------------------------
    
if __name__ == '__main__':
    
    StartTimer = datetime.now()
    TimeStamp  = 'Start Time (hh:mm:ss.ms) {}'.format(StartTimer)
    print(TimeStamp)    
    #-----------------------------------------------------------------
    
    StdOutLogger,LogHandler = GetLogger(__name__,sys.stdout)
         
    PatchesOutputDirectory,\
    ConfigurationFile       = Initialize()
    
    PatchManagerObject      = ProcessPatches(PatchesOutputDirectory,ConfigurationFile)
    
    Terminate(ConfigurationFile,PatchManagerObject)
    
    CloseHandles()
    
    StdOutLogger.info('Done')
             
    #-----------------------------------------------------------------
    TimeElapsed = datetime.now() - StartTimer
    TimeStamp   = 'Time elapsed (hh:mm:ss.ms) {}\n'.format(TimeElapsed)
    print(TimeStamp)
