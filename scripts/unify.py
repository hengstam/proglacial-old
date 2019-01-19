import sys
import archook #T 	he module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import cv2
import hashlib
import numpy as np
import glob, os

def unify (directory):

	print "Unifying lakes from " + directory + "..."

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

	# This is where we trace lakes over for copying them
	tracingpaper = "/temp/tracing_output.shp"
	if arcpy.Exists(tracingpaper):
	    arcpy.Delete_management(tracingpaper)

	# Get some names
	masterlakefile = "/master_lakes/master_lake_file.shp"

	###########################################
	## Define some new types of data structures
	class bubblebath(object):

		data = []

		def add(self, i):

			# Add our incoming group to the dataset
			self.data.append(set(i))

			# Iterate through new things
			for item in i:
				membership = []
				index = -1;

				# Work through each group
				for bubble in self.data:  
					index += 1

				# Work through each group member
					for thing in bubble:

						# If one of our new items matches a group member, remember that group.
						if item == thing:
							membership.append(index)

							# We only need one match per group
							break

				# Now we have a list of things we belong to. We may need to merge those.
				if len(membership) > 1:

					newbubble = set()

					# Merge them all
					for member in membership:
						newbubble = newbubble | self.data[member]

					# Flip and reverse it so we don't change our indices while deleting
					membership.reverse()

					# Delete the old ones
					for member in membership:
						del self.data[member]

					# Add the new one
					self.data.append(newbubble)

				# And now we repeat for the rest of the items

		def read(self):

			# This is what we will eventually spit out
			out = []

			for i in self.data:
				out.append(list(i))

			return out

		def clean(self, size):

			# Initalize the index and a list of things to get rid of
			index = -1
			remove = []

			# Iterate
			for bubble in self.data:
				index += 1;

				# Check if it's too small
				if len(bubble) <= size or size == 0:
					remove.append(index)

			# Now flip the remove list
			remove.reverse()

			# And delete them all
			for i in remove:
				del self.data[i]

	# Make a clean reader
	def reader(text):
		t = str(text)
		return t[20:22]
	def iterreader(arr):
		s = "["
		for a in arr:
			s += reader(a)
			s += ', '
		s = s[:-2]
		s += ']'
		return s
	def twoiterreader(arr):
		s = "["
		for ar in arr:
			s += '['
			for a in ar:
				s += reader(a)
				s += ', '
			s = s[:-2]
			s += '], '
		s = s[:-3]
		s += ']'
		return s

	####################
	## BEGIN BEGIN BEGIN

	# Loop through all folder names
	fns = glob.glob(env.workspace + '/' + directory + '/*.shp')
	for fn in fns:

		# Trim the filename to get the directory component
		newlakes = fn[len(env.workspace):]

		print "Loading from " + newlakes + "..."

		################################################################################
		## Build a database to help us get feature class filenames from the master lakes
		print "Generating dictionary..."

		# Make the dictionary
		refDict = {}

		# Build a cursor so we can get info on the master lakes
		tempcursor = arcpy.da.SearchCursor(masterlakefile, ['FID', 'ref_id'])

		# Iterate through the cursor results and fill the dictionary
		for fid, hashname in tempcursor:
			refDict[fid] = hashname[:hashlength]

		# Delete the cursor
		del tempcursor
		print "Dictionary generated."

		######################################
		## Collect all FIDs and hashes from the new lakes
		newlakeFIDs = {}
		newRefDict = {}

		# Build a cursor so we can get the stuff from the new lakes
		tempcursor = arcpy.da.SearchCursor(newlakes, ['FID', 'lake_id'])

		for temprow in tempcursor:
			# Mark them all good for now
			newlakeFIDs[temprow[0]] = True

			# Load this up
			newRefDict[temprow[0]] = temprow[1]

		del tempcursor

		#################################
		## Prepare to resolve lake merges
		merges = {}

		###############################################
		## Make lists of lakes which are being modified
		lakes_to_add = set()
		lakes_to_remove = set()

		##########################
		## Check for intersections
		print "Checking for intersections..."

		# Make a list of assignments
		assignments = {}

		# Run the master intersection
		arcpy.Intersect_analysis((newlakes, masterlakefile), output, 'ONLY_FID')

		# Get the names of the two FID fields for the output
		fields = arcpy.ListFields(output)
		FID1 = fields[2].baseName
		FID2 = fields[3].baseName

		# Build a cursor which will iterate over the output fields
		cursor = arcpy.da.SearchCursor(output, [FID1, FID2])

		# Build feature layers on the new lake feature classe to enable selection of objects
		arcpy.Delete_management("newlakes_lyr")
		arcpy.MakeFeatureLayer_management(newlakes, "newlakes_lyr")

		# Iterate through the new intersection shapes
		print "Matching new lakes..."
		for row in cursor:

			# Get the saved input FIDs of each intesection
			newlakeFID = row[0]
			masterlake = row[1]

			# Lookup the reference in our handy-dandy dictionary
			lakeRef = '/master_lakes/lakes/' + refDict[masterlake] + '.shp'	

			# This gets either the previous assignments or an empty list and then adds the current assignment to it
			if str(newlakeFID) in assignments:
				assignments[str(newlakeFID)].append(lakeRef)
			else:
				assignments[str(newlakeFID)] = [lakeRef]

			# Prepare to check for duplicates
			eject = False
			tempcursor = arcpy.da.SearchCursor(lakeRef, ['lake_id'])

			# Look through the already-saved lakes
			newRef = newRefDict[newlakeFID];
			for temprow in tempcursor:

				existingHash = temprow[0]

				# Check that we're not adding a duplicate
				if existingHash == newRef:
					eject = True
					break

			del tempcursor

			# Is it a duplicate?
			if eject:
				print 'Trying to add a duplicate lake ' + newRef[:disphashlength] + '. Ignoring.'

			# Nope
			else:

				# Prepare a partial feature class to copy it over (it's just going to be the one lake)
				arcpy.FeatureClassToFeatureClass_conversion(newlakes, env.workspace, tracingpaper, 'FID = ' + str(row[0]))

				# Add this lake to the new feature class
				arcpy.Append_management(tracingpaper, lakeRef, "NO_TEST")

				# Delete the temp shit
				arcpy.Delete_management(tracingpaper)

				# This lake needs to be refreshed
				lakes_to_remove.add(lakeRef)
				lakes_to_add.add(lakeRef)

				print 'Added lake ' + newRef[:disphashlength] + ' to ' + lakeRef + '.'

			# Indicate that this lake has found a home
			newlakeFIDs[newlakeFID] = False

		del cursor

		# Remove the temp file
		arcpy.Delete_management(output)

		print "Matching complete."

		#####################################
		## Make new lakes for new lake shapes 

		# Iterate through all the lakes...
		cursor = arcpy.da.SearchCursor(newlakes, ['FID', 'lake_id'])

		for row in cursor:

			# Check from the dictionary to make sure it's untouched
			if newlakeFIDs[row[0]]:

				# Yay!
				hashID = row[1]
				hashID = hashID[:hashlength]

				# Save it to a brand-new feature class
				myNewLakeFilename = '/master_lakes/lakes/' + hashID + '.shp'
				if arcpy.Exists(myNewLakeFilename):
					print "Skipping making a new lake, file already present."
				else:

					# Make said brand-new feature class
					arcpy.CreateFeatureclass_management(
						env.workspace, 
						myNewLakeFilename, 
						"POLYGON"
					)
					arcpy.AddField_management(myNewLakeFilename, "ID", "LONG")
					arcpy.AddField_management(myNewLakeFilename, "GRIDCODE", "LONG")
					arcpy.AddField_management(myNewLakeFilename, "area", "DOUBLE")
					arcpy.AddField_management(myNewLakeFilename, "centr_x", "DOUBLE")
					arcpy.AddField_management(myNewLakeFilename, "centr_y", "DOUBLE")
					arcpy.AddField_management(myNewLakeFilename, "lake_id", "STRING")
					arcpy.AddField_management(myNewLakeFilename, "date", "LONG")
					arcpy.AddField_management(myNewLakeFilename, "loc1", "SHORT")
					arcpy.AddField_management(myNewLakeFilename, "loc2", "SHORT")

					# Prepare a partial feature class to copy it over (it's just going to be the one lake)
					arcpy.FeatureClassToFeatureClass_conversion(newlakes, env.workspace, tracingpaper, 'FID = ' + str(row[0]))

					# Add this lake to the new feature class
					arcpy.Append_management(tracingpaper, myNewLakeFilename, "NO_TEST")

					# Delete the temp shit
					arcpy.Delete_management(tracingpaper)

					# This needs to be added to the master file
					lakes_to_add.add(myNewLakeFilename)

					print "New lake found! Created a whole new file just for it, we'll call it " + hashID[:disphashlength] + '.'

		# Clean up
		del cursor

		################################################
		## Go through all matched lakes and find mergers

		print "Merge checking..."

		# Make our data structure
		bath = bubblebath()

		# Load them all in
		for assingment in assignments:
			print iterreader(assignments[assingment]) + ' --> ' + twoiterreader(bath.read())
			bath.add(assignments[assingment])

		# Clean the small things (aka a non-merger)
		print "Behold the final bubblebath:"

		bath.clean(1)
		print twoiterreader(bath.read())

		# Merge this stuff
		for bubble in bath.read():

			# Make a new feature class name
			m = hashlib.sha224()

			# Mutate hash using lake names
			for item in bubble:
				m.update(str(item))

			m.update('holla holla')

			# Export it
			hashvalue = m.hexdigest()
			myNewLakeFilename = '/master_lakes/lakes/' + hashvalue[:hashlength] + '.shp'

			del m

			if arcpy.Exists(myNewLakeFilename):
				print myNewLakeFilename
				print "Collision while trying to merge bubbles!!!"
			else:

				print "Bubbles will be merged into " + myNewLakeFilename + "."

				# Make said brand-new feature class
				arcpy.CreateFeatureclass_management(
					env.workspace, 
					myNewLakeFilename, 
					"POLYGON"
				)
				arcpy.AddField_management(myNewLakeFilename, "ID", "LONG")
				arcpy.AddField_management(myNewLakeFilename, "GRIDCODE", "LONG")
				arcpy.AddField_management(myNewLakeFilename, "area", "DOUBLE")
				arcpy.AddField_management(myNewLakeFilename, "centr_x", "DOUBLE")
				arcpy.AddField_management(myNewLakeFilename, "centr_y", "DOUBLE")
				arcpy.AddField_management(myNewLakeFilename, "lake_id", "STRING")
				arcpy.AddField_management(myNewLakeFilename, "date", "LONG")
				arcpy.AddField_management(myNewLakeFilename, "loc1", "SHORT")
				arcpy.AddField_management(myNewLakeFilename, "loc2", "SHORT")

			for item in bubble:

				print "Merging " + item + "..."

				# Append all the other ones 
				arcpy.Append_management(item, myNewLakeFilename, "NO_TEST")

				# Delete the old feature classes
				arcpy.Delete_management(item)

				# This needs to be removed
				lakes_to_remove.add(item)

			# Remove duplicate lakes from the unified feature class
			tempcursor = arcpy.da.UpdateCursor(myNewLakeFilename, ['lake_id'])

			# Make a list of lake IDs. When we find a duplicate we'll delete the dupe one
			IDs = set()

			for row in tempcursor:
				ID = row[0]
				if ID in IDs:				
					tempcursor.deleteRow()
					print "Deleted a duplicate in the merged bubble."
				else:
					IDs.add(ID)

			# Take out the trash
			del tempcursor, IDs

			# Make sure to add the new lake
			lakes_to_add.add(myNewLakeFilename)

			print "Merge successful."

			# Now do it for the others

		####################################################
		## Generate union shapes and update the master files
		print "Beginning master lake file update..."

		if len(lakes_to_add) == 0 and len(lakes_to_remove) == 0:
			print "actually nevermind..."
		else:
			
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

			print "Master lake file updated."
			
		print "Success!"

		# Reset this thing
		bath.clean(0)

# Execute	
if __name__ == "__main__":
	print "Loading script..."
	unify(sys.argv[1])