import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import os, shutil

env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
masterlakefile = "/master_lakes/master_lake_file.shp"

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
print "Master lake file cleared."