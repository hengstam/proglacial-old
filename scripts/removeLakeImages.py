import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import os
from glob import glob

def removeLakeImages (dates):

	print "Removing lake images..."

	print dates

	# Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
	masterlakefile = env.workspace + '/master_lakes/master_lake_file.shp'

	# Open the shape folder directory
	os.chdir(env.workspace + "/master_lakes/lakes/")

	# Iterate through all shapefiles
	for file in glob("*.shp"):
		address = env.workspace + "/master_lakes/lakes/" + file

		# Get the lake images
		arcpy.MakeFeatureLayer_management(address, 'layer')

		for date in dates:
			arcpy.SelectLayerByAttribute_management('layer', "NEW_SELECTION", "date=" + date)
			items = int(arcpy.GetCount_management('layer').getOutput(0))
			if items != 0:
				print "Found " + str(items) + " matching lake images for " + date + " in " + file
				arcpy.DeleteFeatures_management('layer')

		# Clear the layer name
		arcpy.Delete_management('layer')

		# Check if it needs to be removed
		number = int(arcpy.GetCount_management(address).getOutput(0))
		if number == 0:
			print "This bitch empty!"
			arcpy.Delete_management(address)
			print file + " deYEETed."

	print "Success!"
	print "Make sure to run refreshMaster.py to update the master lake files!"

# Execute	
if __name__ == "__main__":
	print "Loading script..."
	removeLakeImages(sys.argv[1:])