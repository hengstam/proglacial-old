import sys
import archook #T 	he module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import cv2
import hashlib
import numpy as np
import glob, os

def refresh ():
	
	# Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
	hashlength = 30
	disphashlength = 12

	# This is where intersection results will be temporarily held
	output = "/temp/intersection_output.shp"
	if arcpy.Exists(output):
	    arcpy.Delete_management(output)

	# Get some names
	masterlakefile = "/master_lakes/master_lake_file.shp"

	####################################################
	## Generate union shapes and update the master files
	print "Beginning master lake file update..."

	# Make a new master lake file
	arcpy.Delete_management(masterlakefile)
	arcpy.CreateFeatureclass_management(
		env.workspace, 
		masterlakefile, 
		"POLYGON"
	)
	arcpy.AddField_management(masterlakefile, "ref_id", "STRING")
	arcpy.AddField_management(masterlakefile, "n", "SHORT")
	arcpy.AddField_management(masterlakefile, "n_real", "SHORT")
	arcpy.AddField_management(masterlakefile, "n_ratio", "SHORT")

	print "Master lake file reset."

	# Build an array for the lakes
	lakearray = []

	# Open the shape folder directory
	os.chdir(env.workspace + "/master_lakes/lakes/")

	# Iterate through all shapefiles
	for file in glob.glob("*.shp"):

		ref_id = file[:-4]

		# Add to the array
		lakearray.append(file)

		# Count how many things the thing has
		number = arcpy.GetCount_management(file)
		dates = set()

		# Iterate through all elements of that lake
		count_cursor = arcpy.da.SearchCursor(file, ['date'])
		for crow in count_cursor:
			dates.add(crow[0])

	    # Make a union of the thing
		arcpy.Dissolve_management(file, output)

		# Get ready to add reference stuff to the thing
		arcpy.AddField_management(output, "ref_id", "STRING")
		arcpy.AddField_management(output, "n", "SHORT")
		arcpy.AddField_management(output, "n_real", "SHORT")
		arcpy.AddField_management(output, "n_ratio", "SHORT")

		# This cursor will let up change up that reference id
		cursor = arcpy.da.UpdateCursor(output, ["ref_id", "n", "n_real", "n_ratio"])

		# Update that thang
		for row in cursor:
			row[0] = ref_id
			row[1] = int(number[0])
			row[2] = len(dates)
			row[3] = row[1]/row[2]
			print "Adding lake", ref_id, "to new master lake file. Has", number[0], "lake images over", row[2], "dates."
			cursor.updateRow(row)

		del cursor

		# Add it to the master lake file
		arcpy.Append_management(output, masterlakefile, 'NO_TEST')

		# Remove the temp file
		arcpy.Delete_management(output)

	print "Success!"

# Execute
if __name__ == "__main__":
	print "Loading script..."
	refresh()