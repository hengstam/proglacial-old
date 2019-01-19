import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
from glob import glob
import cv2

doIndices = False

def makeMultiBand (directory, make_multi_band):

	#Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Set up arc
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env/"
	arcpy.env.overwriteOutput = True

	print "Opening " + env.workspace + '/' + directory + "..."

	# Loop through all folder names
	subdirs = glob(env.workspace + '/' + directory + '/*_ANG.txt')
	for fn in subdirs:

		# Trim the filename to get the directory component
		fn = fn[len(env.workspace) + len(directory) + 2:-8]

		print "Loading from " + str(fn) + "..."

		# Open them
		b = {}
		raster = {}
		for n in range(1, 8):
			b[str(n)] = env.workspace + "/" + directory + "/" + fn + "_B" + str(n) + ".TIF"
			print "Importing band " + str(n) + "..."
			print "Band " + str(n) + " successfully imported."
		print "All bands imported."

		# Start listing what rasters will be used to create the multiband:
		bandlist = b['1'] + ';' + b['2'] + ';' + b['3'] + ';' + b['4'] + ';' + b['5'] + ';' + b['6'] + ';' + b['7']

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
		if make_multi_band:
			print "Generating composite band, this may take a while..."
			arcpy.CompositeBands_management(bandlist, "unclassified_rasters/" + fn + "_compbands.tif")

			# Finish
			print "Success! <env>/unclassified_rasters/" + fn + "_compbands.tif created."

		# Mask time
		print  "Loading OpenCV2, making mask..."

		# Load it into cv2
		mask = cv2.imread(b['1'], cv2.IMREAD_GRAYSCALE)
		ret, mask_b = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
		for i in ['2', '3', '4', '5', '6', '7']:
			otherimg = cv2.imread(b[i], cv2.IMREAD_GRAYSCALE)
			ret, otherimg_b = cv2.threshold(otherimg, 1, 255, cv2.THRESH_BINARY)
			mask_b = cv2.bitwise_and(mask_b, otherimg_b)

		cv2.imwrite(env.workspace + "/unclassified_rasters/" + fn + "_compbands_mask.tif", mask_b)

		print "Success! <env>/unclassified_rasters/" + fn + "_compbands_mask.tif created."

		# Clean up
		del b, raster, bandlist

# Execute
if __name__ == "__main__":
	print "Loading script..."
	makeMultiBand(sys.argv[1], sys.argv[2])