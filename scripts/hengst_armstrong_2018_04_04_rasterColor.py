import numpy as np
import os, sys
from osgeo import gdal
import matplotlib.pyplot as plt
from scipy.stats import norm
import cv2 as cv

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

# Real content now
np.seterr(divide='ignore', invalid='ignore')
bands, geo = loadBands()
 
    
    
def plotWithHistogram (data, index, info, title, hist_data=[], save=True, dpi=300, cmap="RdYlGn", additional_data=[]):   
    index = str(index)
    
    if hist_data==[]:
        hist_data = data
    
    # Plot the data
    plt.figure(dpi = dpi)
    plt.axis('off')
    plt.imshow(data, cmap=plt.get_cmap(cmap))
    plt.clim(0, 1)
    plt.colorbar()
    plt.ylabel("")
    plt.xlabel("")
    plt.title(index + ") "+ title + " (" + info + ")")
    
    # Build the histogram    
    A = hist_data.flatten()  
    
    # Plot the histogram    
    h = plt.axes([0.2425, 0.125, 0.501, 0.2])
    h.patch.set_alpha(0.0)
    h.spines['top'].set_visible(False)
    h.spines['right'].set_visible(False)
    h.spines['left'].set_visible(False)
    h.get_yaxis().set_ticks([])
    #plt.tick_params(labelsize=5)
    vals, bins, patches = plt.hist(A[~np.isnan(A)], bins=512, range=(0,1), facecolor='k', alpha=0.7)
    
    # Plot other stuff 
    if not additional_data==[]:
        g = plt.axes([0.24, 0.112, 0.5755, 0.2])
        g.patch.set_alpha(0.0)
        g.spines['top'].set_visible(False)
        g.spines['right'].set_visible(False)
        g.spines['left'].set_visible(False)
        g.get_yaxis().set_ticks([])
        g.get_yaxis().set_ticks([])
        plt.plot(additional_data[0], additional_data[1]*np.amax(vals), color='r')        
    
    # Show it
    if save==True:
        plt.savefig("C:\\Users\\hengstam\\Desktop\\" + index + "_" + info + '.png')
        plt.close()        
        print "File #" + index + " saved."
    else:
        plt.show()
    
def getLocal(f, x, y, r):
    # Select the data
    return f[y-r:y+r, x-r:x+r]    

def doLocalHists(d, name_type, save=True):
    plotWithHistogram(getLocal(d, 4000, 4500, 400), 1, name_type, "Ice and Snow", save=save)
    plotWithHistogram(getLocal(d, 4400, 1600, 400), 2, name_type, "Vegetation and Lakes", save=save)
    plotWithHistogram(getLocal(d, 4000, 6400, 400), 3, name_type, "Clear Water", save=save)
    plotWithHistogram(getLocal(d, 2500, 5200, 400), 4, name_type, "Turbid Water 1", save=save)
    plotWithHistogram(getLocal(d, 4900, 2600, 400), 5, name_type, "Turbid Water 2", save=save)
    plotWithHistogram(getLocal(d, 4950, 5400, 400), 6, name_type, "Turbid Water 3", save=save)
    plotWithHistogram(getLocal(d, 1500, 3500, 400), 7, name_type, "Unvegetated Rocky Stuff", save=save)
    plotWithHistogram(getLocal(d, 1300, 4900, 400), 8, name_type, "Postglacial Lake", save=save) 
    
def doLocalColor(r, g, b, save=True):             
    d = falseColor(r, g, b)
    info = "falseColor_"+r+'-'+g+'-'+b
    
    def plotty (data, index, title): 
        index = str(index)
        
        # Plot the data
        plt.figure(dpi = 300)
        plt.axis('off')
        plt.imshow(data)
        plt.ylabel("")
        plt.xlabel("")
        plt.title(index + ") "+ title + " (" + info + ")")
    
        # Show it
        if save==True:
            plt.savefig("C:\\Users\\hengstam\\Desktop\\" + index + "_" + info + '.png')
            plt.close()        
            print "File #" + index + " saved."
        else:
            plt.show()
    
    plotty(getLocal(d, 4000, 4500, 400), 1, "Ice and Snow")
    plotty(getLocal(d, 4400, 1600, 400), 2, "Vegetation and Lakes")
    plotty(getLocal(d, 4000, 6400, 400), 3, "Clear Water)")
    plotty(getLocal(d, 2500, 5200, 400), 4, "Turbid Water 1")
    plotty(getLocal(d, 4900, 2600, 400), 5, "Turbid Water 2")
    plotty(getLocal(d, 4950, 5400, 400), 6, "Turbid Water 3")
    plotty(getLocal(d, 1500, 3500, 400), 7, "Unvegetated Rocky Stuff")
    plotty(getLocal(d, 1300, 4900, 400), 8, "Postglacial Lake")

# Filters
def GNDWI ():
    return normalize((bands['5'] + bands['3'] - bands['6']) / (bands['5'] + bands['3'] + bands['6']))

def MassNDWI ():
    return normalize((bands['1'] + bands['2'] + bands['3'] + bands['4'] - bands['6'] - bands['5']) / (bands['1'] + bands['2'] + bands['3'] + bands['4'] + bands['6'] + bands['5']))

def NDWI ():
    return normalize((bands['3'] - bands['5']) / (bands['3'] + bands['5']))

def NDSI ():
    return normalize((bands['2'] - bands['4']) / (bands['2'] + bands['4']))

# Make the filters
def waterFilter (plot=False):
    s1 = 0.05
    s2 = 0.01
    t1 = 0.80
    t2 = 0.53
    filter1 = norm(loc=t1, scale=s1)
    filter2 = norm(loc=t2, scale=s2)
    
    # Process Data
    gndwi = GNDWI()
    gndwi_fuzz = filter1.cdf(gndwi)
    
    mndwi = MassNDWI()
    mndwi_fuzz = filter2.cdf(mndwi)
    
    # Plot it
    if plot:
        X = np.arange(0, 1, 1.0/512.0)
        plotRaster(gndwi, "1) GNDWI")
        plotWithHistogram(gndwi_fuzz, 2, "t=" + str(t1) + " , s="+str(s1), "GNDWI", save=False, cmap="Greys_r", hist_data=gndwi, additional_data=(X, filter1.cdf(X)))
        plotRaster(mndwi, "3) MassNDWI")
        plotWithHistogram(mndwi_fuzz, 4, "t=" + str(t2) + " , s="+str(s2), "MassNDWI", save=False, cmap="Greys_r", hist_data=mndwi, additional_data=(X, filter2.cdf(X)))
        plotRaster(gndwi_fuzz*mndwi_fuzz, "5) Combined Fuzzy Threshold", dpi=1000, cmap="Greys_r")
    else:
        return gndwi_fuzz*mndwi_fuzz
    
# Numpy to CV
def np2cv (data):
    return (data*255).astype(np.uint8)

# Save file
from libtiff import TIFF
def saveTiff (data, name):
    tiff = TIFF.open('C:/Users/hengstam/Desktop/' + name + 'tiff', mode='w')
    tiff.write_image(data)
    
    
#img = np2cv(waterFilter())
#ret1, th1 = cv.threshold(img, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
#ret2, th2 = cv.threshold(cv.GaussianBlur(img, (31, 31), 0), 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
#plotRaster(th1, dpi=800)
#plotRaster(th2, dpi=800)


saveTiff(NDSI(), 'ndsi')



#plotFalseColor('6', '5', '4', dpi=800)

#plotRaster(diff(bands['3'] + bands['2'], 2*bands['5']))
#plotRaster(diff(bands['10'], bands['4'])) # Rivers?

#plotRasterColor(bands['2'], bands['3'], bands['4'], "2-3-4") # Nat Color
#plotRasterColor(bands['6'], bands['5'], bands['4'], "6-5-4") # False Color
#plotRasterColor(bands['5'], bands['4'], bands['3'], "5-4-3") # Standard false color
#plotRasterColor(bands['7'], bands['6'], bands['5'], "7-6-5") # atmospheric penetration
#plotRasterColor(bands['10'], bands['7'], bands['3'], "10-7-3")
#plotRasterColor(bands['5'], bands['2'], bands['3'], "5-2-3")
#plotRasterColor(bands['7'], bands['5'], bands['1'], "7-5-1")
#plotRasterColor(bands['10'], bands['6'], bands['5'], "10-6-5")
#plotRasterColor(bands['5'], bands['6'], bands['4'], "5-6-4")
#plotRaster((MNDWI()-MNDSI()+NDWI()))

#a = normalize(diff(bands['2'] + bands['3'] + bands['1'] + bands['4'], 2*(bands['7'] + bands['6'])))
#b = GNDSI()
#plotRaster(a+0.4*bands['9'], 'Water')

#plotRaster(b, 'Ice')
#plotRaster(a-2*b + 0.2+bands['9'], 'Stuff')

#plotRaster(crop(10, diff(bands['2'] + bands['3'] + bands['1'] + bands['4'], 2*(bands['7'] + bands['6'])) - GNDSI() - 0.5*NDCI() + bands['9'], True, True))
#plotRaster(GNDWI(), "Water (t=0.75)")
#splotRaster(GNDSI() > 0.75, "Ice/Snow (t=0.75)")
#plotRaster(NDCI(), "Clouds (t=0.7)")

#plotRaster(bitFilter(), "Bitwise Threshold Filter")
#plotRasterColor(GNDWI(), GNDSI(bands), NDCI(bands))


#plotRaster((NDWI() > -0.1).astype(np.int8) - 2*(NDSI() > 0.2).astype(np.int8), "NDWI")
#plotRaster((MNDWI() > -0.1).astype(np.int8) - 2*((NDSI() > 0.2) & (bands['4'] > 0.2)).astype(np.int8))

































