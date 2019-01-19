import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import os, shutil

env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
masterlakefile = "/master_lakes/master_lake_file.shp"

# Library
folder = env.workspace + '/master_lakes/lakes/'
tempfolder = env.workspace + '/temp/'

# Delete everything in the library
for the_file in os.listdir(folder):

	# Find file
    file_path = os.path.join(folder, the_file)

    try:
    	# Delete files
        if os.path.isfile(file_path):
            os.unlink(file_path)

    except Exception as e:
    	# What's wrong?
        print(e)

# Delete everything in the library
for the_file in os.listdir(tempfolder):

    # Find file
    file_path = os.path.join(tempfolder, the_file)

    try:
        # Delete files
        if os.path.isfile(file_path):
            os.unlink(file_path)

    except Exception as e:
        # What's wrong?
        print(e)

# Recreate master
arcpy.Delete_management(masterlakefile)
arcpy.CreateFeatureclass_management(
	env.workspace, 
	masterlakefile, 
	"POLYGON"
)
arcpy.AddField_management(masterlakefile, "ref_id", "STRING")
arcpy.AddField_management(masterlakefile, "n", "SHORT") 

# Finished.
print "Lake files completely reset."