import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
from glob import glob

doIndices = False

def makeMultiBand (directory):

	#Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Set up arc
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env/"
	arcpy.env.overwriteOutput = True

	# Get folder	
	#print "What subfolder contains the files?"
	#fn = raw_input();
	#print "Do you want to process these files? (y/n)"
	do_process = 'y' #raw_input()

	# Loop through all folder names
	subdirs = glob(env.workspace + '/' + directory + '/*_ANG.txt')
	for fn in subdirs:

		# Trim the filename to get the directory component
		fn = fn[len(env.workspace) + len(directory) + 2:-8]

		print "Loading from " + str(fn) + "..."

		# Open them
		b = {}
		raster = {}
		for n in range(1, 12):
			b[str(n)] = env.workspace + "/" + directory + "/" + fn + "_B" + str(n) + ".TIF"
			print "Importing band " + str(n) + "..."
			if do_process == "y":
				# Must generate histograms for percentage clipping. We skip some pixels both dimensions while sampling to speed it up.
				# arcpy.CalculateStatistics_management(b[str(n)], "32", "32")
				# Clip it
				# arcpy.GenerateExcludeArea_management(b[str(n)], b[str(n)], "16_BIT", "HISTOGRAM_PERCENTAGE", 255, 255, 255, 255, 0, 255, 255, 255, 5, 95)
				raster[str(n)] = arcpy.sa.Raster(b[str(n)])
			print "Band " + str(n) + " successfully imported."
		print "All bands imported."

		# Start listing what rasters will be used to create the multiband:
		bandlist = b['1'] + ';' + b['2'] + ';' + b['3'] + ';' + b['4'] + ';' + b['5'] + ';' + b['6'] + ';' + b['7'] + ';' + b['9']

		if doIndices:
			# Make differential indices
			indices = ['NDVI', 'NDWI', 'NDSI']

			print "Generating indices..."
			raster['NDVI'] = arcpy.sa.Divide(arcpy.sa.Float(raster['4'] - raster['3']), arcpy.sa.Float(raster['4'] + raster['3']))
			raster['NDWI'] = arcpy.sa.Divide(arcpy.sa.Float(raster['3'] - raster['5']), arcpy.sa.Float(raster['3'] + raster['5']))
			raster['NDSI'] = arcpy.sa.Divide(arcpy.sa.Float(raster['3'] - raster['6']), arcpy.sa.Float(raster['3'] + raster['6']))
			print "Indices sucessfully generated."

			# Save them
			for i in indices:
				b[i] = env.workspace + "/" + directory + "/" + fn + "_" + i + ".tif"
				raster[i].save(b[i])
				print "Index " + i + " saved."
			print "All indices saved."
			
			# Update the bandlist
			bandlist = b['NDVI'] + ';' + b['NDWI'] + ';' + b['NDSI'] + ';' + bandlist
			
		# Make and save it	
		print "Generating composite band, this may take a while..."
		arcpy.CompositeBands_management(bandlist, "unclassified_rasters/" + fn + "_compbands.tif")

		# Finish
		print "Success! <env>/unclassified_rasters/" + fn + "_compbands.tif created."

		# Clean up
		del b, raster, bandlist

# Execute
if __name__ == "__main__":
	print "Loading script..."
	makeMultiBand(sys.argv[1])