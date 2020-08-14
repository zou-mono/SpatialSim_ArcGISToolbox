# -*- coding: gbk -*-

import arcpy
import os
import csv
import codecs
import sys
import random
import numpy as np

reload(sys)
sys.setdefaultencoding('utf8')

print(range(10)[2:])

a = np.array([1,3,4,5])
b = np.array([-1,-2,-3,-4])
c = np.array([1,3,4,5])
print(a[0:2])
print(np.concatenate(([1],[21], b, c, a[1:2]), axis=0))


# output = r"E:\Source code\空间模拟\SpatialSim_ArcGISToolbox\res.gdb"
# print(arcpy.env.workspace)
# print(arcpy.Describe(output).name)
# print(arcpy.Describe(output).path)
# print(arcpy.Describe(output).dataType)
# print(arcpy.Describe(output).workspaceType)
#
# arcpy.env.workspace = r"E:\Source code\空间模拟\SpatialSim_ArcGISToolbox"
# output = r"E:\Source code\空间模拟\SpatialSim_ArcGISToolbox\buildingStat.shp"
# print([f.name for f in arcpy.ListFields("buildingStat.shp")])