import sys

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
			if len(bubble) <= size:
				remove.append(index)

		# Now flip the remove list
		remove.reverse()

		# And delete them all
		for i in remove:
			del self.data[i]




# Execute
if __name__ == "__main__":
	bath = bubblebath()
	bath.add([1, 2, 3])
	bath.add([4, 5])
	bath.add([6])
	print bath.read()
	bath.clean(1)
	print bath.read()
	bath.clean(2)
	print bath.read()