import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
from glob import glob


def objectifyRaster (directory, sigfilename):

	#Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
	classified_location = env.workspace + "/classified_rasters"

	# Make sure we can mess with stuff
	arcpy.env.overwriteOutput = True

	# Load the signature file
	sigfile = env.workspace + '/' + sigfilename + '.gsg'

	# Iterate through all files
	files = glob(env.workspace + '/' + directory + '/*_compbands.tif')
	for rawRaster in files:

		rawRasterName = rawRaster[len(env.workspace) + 1:]
		maskraster = rawRasterName[:-4] + '_mask.tif'

		print maskraster

		# Set up our output
		outputname = rawRasterName[len(directory) + 1:-4-10] + "_classified"
		classifiedraster = classified_location + '/' + outputname + '.tif'
		shapes = "classified_polygons/" + outputname + ".shp"

		if arcpy.Exists(shapes):
		    arcpy.Delete_management(shapes)

		print "Converting raster " + rawRasterName + " into " + shapes + '...'


		#####################################################
		#####################################################
		####                                             ####
		####            CLASSSIFY IT NOW PLZ	         ####
		####                                             ####
		#####################################################
		#####################################################

		print "Classifying raster with sig file " + sigfile[len(env.workspace) + 1:] + ". This may take some time..."

		# Run the classification
		raster = arcpy.sa.MLClassify(rawRasterName, sigfile, "0.0")

		# Save it
		raster.save(classifiedraster)

		print "Maximum likelihood classification raster saved to " + classifiedraster[len(env.workspace) + 1:] + '!'

		
		#####################################################
		#####################################################
		####                                             ####
		####            OBJECTIFY IT NOW PLZ	         ####
		####                                             ####
		#####################################################
		#####################################################

		rasterWaterOnly = arcpy.sa.Con(raster, 1, 0, "Value <= 2")
		rasterWaterOnly.save(env.workspace + "/temp/temp.tif")

		# Remove artifacts
		del raster, rasterWaterOnly
		print "Raster successfully imported."

		##############################################
		## Apply morphological operations to the water
		print "Loading OpenCV2..."

		# Load it into cv2
		img = cv2.imread(env.workspace + "/temp/temp.tif", cv2.IMREAD_GRAYSCALE)

		print "Masking with " + maskraster + "..."

		mask = cv2.imread(maskraster, cv2.IMREAD_GRAYSCALE)
		img_masked = cv2.bitwise_and(img, mask)

		print "Applying morphological opening operations..."

		# Apply the two operations
		opening = cv2.morphologyEx(img_masked, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
		closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

		# Save it
		cv2.imwrite(env.workspace + "/temp/temp.tif", closing)

		print "Raster successfully opened."

		#############################
		## Reload the modified raster

		# Load it
		raster = arcpy.Raster(env.workspace + "/temp/temp.tif") 

		# Clear the falses out for compatability with arcpy
		raster = arcpy.sa.SetNull(raster != 1, raster)

		###########################
		## Make the output
		print "Preparing shapefile output..."

		# Make a new feature class
		arcpy.CreateFeatureclass_management(
			env.workspace, 
			shapes, 
			"POLYGON"
		)

		# Convert it
		print "Converting raster to polygons..."

		arcpy.RasterToPolygon_conversion(
			raster, 
			shapes, 
			"NO_SIMPLIFY"
		)

		print "Raster successfully converted."

		#####################################################
		#####################################################
		####                                             ####
		####             PROCESS IT NOW PLZ	             ####
		####                                             ####
		#####################################################
		#####################################################

		# Our file to be processed
		pshapes = 'processed_polygons/' + outputname + '.shp'

		# Copy it over
		print "Processing " + shapes + " as " + pshapes + "..."
		arcpy.CopyFeatures_management(shapes, pshapes)

		# Get the date and location
		date = int(outputname[17:25])
		loc = (int(outputname[10:13]), int(outputname[13:16]))
		print "Date:", date, "Location:", loc

		###################################
		## Calculate area and get centroids
		print "Detailing shapefiles..."

		# Add fields
		arcpy.AddField_management(pshapes, "area", "DOUBLE")
		arcpy.AddField_management(pshapes, "centr_x", "DOUBLE")
		arcpy.AddField_management(pshapes, "centr_y", "DOUBLE")
		arcpy.AddField_management(pshapes, "lake_id", "STRING")
		arcpy.AddField_management(pshapes, "date", "LONG")
		arcpy.AddField_management(pshapes, "loc1", "SHORT")
		arcpy.AddField_management(pshapes, "loc2", "SHORT")

		# Build a cursor to set our new fields
		cursor = arcpy.da.UpdateCursor(pshapes, ["SHAPE@AREA", "SHAPE@TRUECENTROID", "area", "centr_x", "centr_y", "date", "loc1", "loc2"])

		# Start summing area
		areaTotal = 0

		# Work through all pshapes in the feature class
		for row in cursor:

			# Running total of area
			areaTotal = row[0] + areaTotal

			# Write area value 
			row[2] = row[0] 

			# Write centroid values 
			row[3] = row[1][0] 
			row[4] = row[1][1]

			# Write date and location
			row[5] = date
			row[6] = loc[0]
			row[7] = loc[1]

			# Save it
			cursor.updateRow(row)

		# Clean up cursor objects
		del row, cursor 

		print "Shapefiles successfully detailed."

		################################################
		## Only save large polygons (more than 0.2 km^2)
		print "Removing small polygons..."

		arcpy.MakeFeatureLayer_management(pshapes, "pshapes_lyr")
		arcpy.SelectLayerByAttribute_management("pshapes_lyr", "NEW_SELECTION", "area < 200000")
		arcpy.DeleteFeatures_management("pshapes_lyr")
		print "Small polygons successfully removed."

		###########################
		## Name the remaining lakes
		print "Naming lakes..."

		# Make a cursor to update the stuff
		cursor = arcpy.da.UpdateCursor(pshapes, ["SHAPE@AREA", "SHAPE@TRUECENTROID", "lake_id"])

		# n is used to count the number of lakes, which is displayed at the end of this script.
		n = 0 

		# Go through all lakes in the feature class
		for row in cursor:	

			# Counting works like this
			n += 1

			# Make hash
			m = hashlib.sha224()

			# Use centroid, area, and date to mutate hash
			m.update(str(row[1]))
			m.update(str(row[1][0]))
			m.update(str(row[1][1]))
			m.update(str(date))

			# Save it
			row[2] = m.hexdigest()

			cursor.updateRow(row)

		# Clean up cursor objects
		del cursor 

		# IO
		print "success! " + str(n) + " lakes found and named." 	
		print str(areaTotal) + "m^2 total lake area."

# Execute
if __name__ == "__main__":
	print "Loading script..."
	objectifyRaster(sys.argv[1], sys.argv[2])