import numpy as np
from osgeo import gdal
from PIL import Image
import glob, os

for infile in glob.glob("C:\\Users\\hengstam\\Desktop\\Research\\hengst_env\\rasters\\LC08_L1TP_067017_20160714_20170222_01_T1\\*.TIF"):
	file, ext = os.path.splitext(infile)
	dataset = gdal.Open(file + ext)
	data = dataset.ReadAsArray(4400, 3000, 3300, 2200)
	im = Image.fromarray(data)
	im.save(file + "_copy" + ext)