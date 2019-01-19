import numpy as np
import os, sys
from osgeo import gdal
import matplotlib.pyplot as plt
import scipy
# K-means
from copy import deepcopy

# Raster processing functions
def normalize (d):
    u = d - np.nanmin(d)
    return u / np.nanmax(u)

def crop (n, d, upper, lower):
    n = n/2
    if upper:
        d[d > np.nanpercentile(d, 100-n)] = np.nanpercentile(d, 100-n)
    if lower:
        d[d < np.nanpercentile(d, n)] = np.nanpercentile(d, n)
    return d

# Plotting functions 
def plotRaster (d, title="", cmap="RdYlGn", dpi=250, color=True):
    plt.figure(dpi=dpi)
    plt.axis('off')
    plt.imshow(d, cmap=plt.get_cmap(cmap))
    if color==True:
        plt.colorbar()
    plt.ylabel("")
    plt.xlabel("")
    plt.title(title)
    plt.show()
    
def falseColor (r, g, b):
    return np.dstack((normalize(bands[r]), normalize(bands[g]), normalize(bands[b])))
    
def plotFalseColor (r, g, b, dpi=250):
    plotRaster(falseColor(r, g, b), r + '-' + g + '-' + b, color=False, cmap=None, dpi=dpi)
    
def plotColor (d, dpi=250):
    plotRaster(d, "", color=False, cmap=None, dpi=dpi)
    
# Geospatial functions   
def geoToPixel (f, y, x):
    print f.GetGeoTransform()
    # Get the raw geospatial data
    # ulx, y is the upper left corner, lrx, y is the lower right corner
    ulx, xres, xskew, uly, yskew, yres = f.GetGeoTransform()
    lrx = ulx + (f.RasterXSize * xres)
    lry = uly + (f.RasterYSize * yres)
    print ((lrx, ulx), (lry, uly))
    
def loadBands ():
    
    def getPath ():
        # path = raw_input("Please provide a valid path to the FOLDER CONTAINING full Landsat 8 raster data: (n to exit) ")
        path = "C:\Users\hengstam\Desktop\LC08_L1TP_067017_20150813_20170226_01_T1"
        if path.endswith('\\') is False:
            path = path + '\\'
        return path
    
    def checkDirectory (path):
        
        bandPaths = {}
        failure = False
        
        # This makes sure that all bands required are present in the directory
        for index in ['1','2','3','4','5','6','7','9','10','11']:            
            for filename in os.listdir(path):                
                # Make sure that there's only one file that looks right
                if filename.endswith('B'+index+'.tif') or filename.endswith('B'+index+'.TIF'):
                    if index not in bandPaths:
                        bandPaths[index] = filename
                    else:
                        failure = True            
            # Make sure we put something in
            if index not in bandPaths: 
                failure = True
        
        # Unless we couldn't find a band or we found too many, return our files
        if failure:
            return False
        else: 
            return bandPaths    
    
    # Load the directory
    bandPaths = False
    firstTry = True
    
    # Verify it
    while bandPaths is False:
        
        # Display a disappointment message if needed
        if firstTry == False:
            print "That didn't work. Try again?"
            
        # Get the file path
        path = getPath()
        firstTry = False
        
        # Handle the given input
        if path == "n":
            sys.exit("Cancelled.")
        else:
            bandPaths = checkDirectory(path)    
            
    # Success
    bands = {}
    geo = {}
    for i, v in bandPaths.items():
        # Open it
        geo[i] = gdal.Open(path + v)     
        
        # Process it into a raster
        bands[i] = geo[i].ReadAsArray().astype(np.float64)
        bands[i][bands[i] == 0] = np.nan        
        
    print "All bands loaded."
                
    return (bands, geo)

def getLocalTuple(f, l):
    x = l[0]
    y = l[1]
    r = l[2]
    # Select the data
    return f[y-r:y+r, x-r:x+r]    
    
# Real content now
np.seterr(divide='ignore', invalid='ignore')
bands, geo = loadBands()

###################
# Filtering stuff #
###################

# Make filters
def diff (a, b):
    return normalize((a-b)/(a+b))

def rediff (a, b, c, d):
    return (a-b)*(c+d)/(a+b)/(c-d)

def LAND ():
    return diff(bands['5'], bands['4'])

def NDSI ():
    return diff(bands['3'], bands['6'])

def MNDSI ():
    return diff(bands['4'], bands['6'])

def GNDSI (): # Good ice detection
    return diff(bands['5'] + bands['3'], 2*bands['6'])

def NDWI ():
    return diff(bands['3'], bands['5'])

def MNDWI ():
    return diff(bands['2'], bands['5'])

def GNDWI (): # Deep-water detection?
    d = diff(bands['11'] + bands['2'], 2*bands['5'])
    d[bands['11'] == 0] = np.nan
    return d

def NDVI ():
    return diff(bands['4'], bands['3'])

def NDCI (): #Clouds
    d = diff(bands['5'] + bands['6'], 2*bands['10'])
    d[bands['10'] == 0] = np.nan
    return d

def EWI ():
    return diff(MNDWI(bands), NDVI(bands))

def AWEI ():
    b5 = bands['5']
    b2 = bands['2']
    b4 = bands['4']
    b7 = bands['7']
    return normalize(4*(b2 - b5) - (0.25*b4 + 2.75*b7))

def AWEI_sh ():
    b1 = bands['1']
    b5 = bands['5']
    b2 = bands['2']
    b4 = bands['4']
    b7 = bands['7']
    return normalize(b1 + 2.5*b2 - 1.5*(b4 + b5) - 0.25*b7)

def MassNDWI ():
    return diff(bands['2'] + bands['3'] + bands['1'] + bands['4'], 2*(bands['7'] + bands['6']))

def MOWI ():
    b1 = bands['1'] * -0.969616734045172
    b2 = bands['2'] * 2.19807138881102
    b3 = bands['3'] * 5.85814134568662
    b4 = bands['4'] * 0.370296018291466
    b5 = bands['5'] * -8.72362757074720
    b6 = bands['6'] * -4.33503214968681
    b7 = bands['7'] * 2.64552671963812
    b10 = bands['10'] * 1.51971484483010
    b11 = bands['11'] * 0.593968608786066
    b9 = bands['9'] * -0.906978774853697
    return b1 + b2 + b3 + b4 + b5 + b6 + b7 + b9 + b10 + b11

def bitFilter ():
    d = (GNDWI(bands) > 0.75).astype(np.int8) + 2*(GNDSI() > 0.55).astype(np.int8) + 4*(NDCI() > 0.6).astype(np.int8)
    d = d.astype(np.float64)
    d[bands['1'] == 0] = np.NaN
    return d

def getLocal(f, x, y, r):
    # Select the data
    return f[y-r:y+r, x-r:x+r]    


#################
# K-means stuff #
#################
    
def dist(a1, a2):
    try:
        return scipy.spatial.distance.euclidean(a1, a2)
    except ValueError:
        print(a1)
        print(a2)

# Set location
loc = (1300, 4900, 3)
DPI = 100

# Number of clusters
k = 2

# Bands to look at
kbands = [
        bands['1'],
        bands['2'],
        bands['3'],
        bands['4'],
        bands['5'],
        bands['6'],
        bands['7'],
        bands['9'],        
    ]

# Load data
plotColor(getLocalTuple(falseColor('6', '5', '4'), loc), dpi=DPI);
dim = []
for i in kbands:
    dim.append(getLocalTuple(normalize(i), loc).flatten())
D = np.array(list(zip(*dim)))
# N-dimensional coordinates of random centroids
c = []
for i in range(0, len(dim)):
    c.append(np.random.random_sample(size=k))
C = np.array(list(zip(*c)), dtype=np.float32)

print D.shape
print C.shape

print D
print C
# To store the value of centroids when it updates
C_old = np.zeros(C.shape)
# Cluster Lables(0, 1, 2)
clusters = np.zeros(len(D))

# Loop will run till the error becomes zero
distance = np.zeros(k)
error = 1
iterations = 0
while error > 0:
    iterations += 1
    # Assigning each value to its closest cluster
    for i in range(loc[2] * loc[2]):
        for j in range(k):
            print i
            print j
            distance[j] = dist(D[i, :], C[j, :])
        clusters[i] = np.argmin(distance)
        
    # Storing the old centroid values
    C_old = deepcopy(C)
    
    # Finding the new centroids by taking the average value
    for i in range(k):
        points = [D[j] for j in range(len(D)) if clusters[j] == i]
        C[i] = np.mean(points, axis=0)
        
    # Calculate error
    error = 0
    for i in range(k):
        error += dist(C_old[i], C[i])
        
    print("Iteration: " + iterations + ", Error: " + error)

# Plot it pixelmapped by centroid
plotRaster(clusters.reshape((loc[2] * 2, loc[2] * 2)), dpi=DPI);




