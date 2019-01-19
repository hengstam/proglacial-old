import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
import csv
from glob import glob


def classify (directory, sigfile):

	#Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"

	arcpy.env.overwriteOutput = True

	# Iterate
	rasters = glob(env.workspace + '/' + directory + '/*.tif')
	for raster in rasters:

		MLClassify(raster, sigfile)

# Execute
if __name__ == "__main__":
	print "Loading script..."
	classify(sys.argv[1], sys.argv[2])