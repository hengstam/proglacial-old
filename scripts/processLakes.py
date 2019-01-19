import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
import csv
from glob import glob


def processLakes (directory):

	#Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"

	arcpy.env.overwriteOutput = True

	files = glob(env.workspace + '/' + directory + '/*.shp')
	for ogshapes in files:

		# Our file to be processed
		ogshapes = ogshapes[len(env.workspace)+1:]
		name = ogshapes[len(directory)+1:]
		shapes = 'processed_polygons/' + name

		# Copy it over
		print "Processing " + ogshapes + " as " + shapes + "..."
		arcpy.CopyFeatures_management(ogshapes, shapes)

		# Get the date and location
		date = int(name[17:24])
		loc = (int(name[10:12]), int(name[13:15]))
		print date, loc

		###################################
		## Calculate area and get centroids
		print "Detailing shapefiles..."

		# Add fields
		arcpy.AddField_management(shapes, "area", "DOUBLE")
		arcpy.AddField_management(shapes, "centr_x", "DOUBLE")
		arcpy.AddField_management(shapes, "centr_y", "DOUBLE")
		arcpy.AddField_management(shapes, "lake_id", "STRING")
		arcpy.AddField_management(shapes, "date", "SHORT")
		arcpy.AddField_management(shapes, "loc", "SHORT")

		# Build a cursor to set our new fields
		cursor = arcpy.da.UpdateCursor(shapes, ["SHAPE@AREA", "SHAPE@TRUECENTROID", "area", "centr_x", "centr_y", "date", "loc"])

		# Start summing area
		areaTotal = 0

		# Work through all shapes in the feature class
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
			row[6] = loc

			# Save it
			cursor.updateRow(row)

		# Clean up cursor objects
		del row, cursor 

		print "Shapefiles successfully detailed."

		################################################
		## Only save large polygons (more than 0.1 km^2)
		print "Removing small polygons..."

		arcpy.MakeFeatureLayer_management(shapes, "shapes_lyr")
		arcpy.SelectLayerByAttribute_management("shapes_lyr", "NEW_SELECTION", "area < 500000")
		arcpy.DeleteFeatures_management("shapes_lyr")
		print "Small polygons successfully removed."

		###########################
		## Name the remaining lakes
		print "Naming lakes..."

		# Make a cursor to update the stuff
		cursor = arcpy.da.UpdateCursor(shapes, ["SHAPE@TRUECENTROID", "lake_id"])

		# n is used to count the number of lakes, which is displayed at the end of this script.
		n = 0 

		# Go through all lakes in the feature class
		for row in cursor:	

			# Counting works like this
			n += 1

			# Make hash
			m = hashlib.sha224()

			# Use centroid to mutate hash
			m.update(str(row[0][0]))
			m.update(str(row[0][1]))

			# Save it
			row[1] = m.hexdigest()

			cursor.updateRow(row)

		# Clean up cursor objects
		del cursor 

		# IO
		print "success! " + str(n) + " lakes found and named." 	
		print str(areaTotal) + "m^2 total lake area."

# Execute
if __name__ == "__main__":
	print "Loading script..."
	processLakes(sys.argv[1])