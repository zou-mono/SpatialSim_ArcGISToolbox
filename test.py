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

output = r"E:\Source code\空间模拟\SpatialSim_ArcGISToolbox\res.gdb"
print(arcpy.env.workspace)
print(arcpy.Describe(output).name)
print(arcpy.Describe(output).path)
print(arcpy.Describe(output).dataType)
print(arcpy.Describe(output).workspaceType)