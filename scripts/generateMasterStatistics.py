import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
import csv	
from glob import glob


def generateMasterStatistics (threshold, ratio_threshold, output):

	print "Generating lake statistics..."

	# Get licensed
	if arcpy.CheckExtension("Spatial"):  
	    arcpy.CheckOutExtension("Spatial")  
	else:  
	    print "No SA licence"  
	    exit  
		
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/Research/hengst_env"
	masterlakefile = env.workspace + '/master_lakes/master_lake_file.shp'
	file = env.workspace + '/' + output

	# An empty array to hold lake data
	data = {}
	dates = set()
	skips = 0

	# Iterate through all lakes in the master lake
	cursor = arcpy.da.UpdateCursor(masterlakefile, ['ref_id', 'n', 'n_real', 'n_ratio'])
	for row in cursor:

		if int(row[2]) <= int(threshold):
			skips += 1
			continue
		if int(row[3]) > int(ratio_threshold):
			skips += 1
			continue

		ref_id = row[0]

		lake = env.workspace + '/master_lakes/lakes/' + ref_id + '.shp'

		lakeData = {}

		# Iterate through all elements of that lake
		lakecursor = arcpy.da.SearchCursor(lake, ['date', 'area'])
		for lakerow in lakecursor:
			date = lakerow[0]
			area = lakerow[1]

			dates.add(date)
			lakeData[date] = lakeData.get(date, 0) + area

		# Save it
		data[ref_id] = lakeData

	print "Skipped " + str(skips) + " small lakes."

	print "Exporting results to " + file + "..."

	with open(file, 'wb') as csvfile: 

		w = csv.writer(csvfile, delimiter=',')
		
		dates = list(dates)
		dates.sort()

		header = ['Lake Name']
		header.extend(dates);
		w.writerow(header)

		# Iterate all stuff
		for lake, datum in data.items():
			stuff = [str(lake)]

			# Iterate through all dates
			for date in dates:
				stuff.append(datum.get(date, ''))

			w.writerow(stuff)

	print "All lake info saved."


# Execute	
if __name__ == "__main__":
	print "Loading script..."
	generateMasterStatistics(sys.argv[1], sys.argv[2], sys.argv[3])