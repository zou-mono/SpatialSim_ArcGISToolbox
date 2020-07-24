# -*- coding: utf-8 -*-

import click
import time
import os
import gdal
from osgeo import ogr
import logging

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s]- %(message)s')

@click.command()
@click.option(
    '--construction', '-c',
    help='输入建设用地方案图层.',
    required=True)
@click.option(
    '--statutory', '-s',
    help='输入法定图则图层.',
    required=True)
def main(construction, statutory):
    # clip(statutory, construction)
    # erase(construction, statutory)
    # clip2(statutory, construction)
    clip_gpkg(statutory, construction)


def clip2(input, clip):
    start = time.time()

    driverName = "ESRI Shapefile"
    driver = ogr.GetDriverByName(driverName)
    inDataSource = driver.Open(input, 0)
    inLayer = inDataSource.GetLayer()

    print(inLayer.GetFeatureCount())

    # inputGeo = loadGeometry(inLayer)

    ## Clip
    inClipSource = driver.Open(clip, 0)
    inClipLayer = inClipSource.GetLayer()
    # print(inClipLayer.GetFeatureCount())

    i = 0
    pFeat = inLayer.GetNextFeature()
    while pFeat is not None:
        pGeom = pFeat.GetGeometryRef()

        # inClipLayer.ResetReading()
        inClipLayer.SetSpatialFilter(pGeom)
        # pClipGeo = pGeom.Intersection(poClipGeo)
        multi = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in inClipLayer:
            pGeo = feature.GetGeometryRef()
            multi.AddGeometry(pGeo)

        pGeo = multi.UnionCascaded()
        if pGeo is not None:
            pResGeo = pGeom.Intersection(pGeo)
            # if pResGeo is not None:
            #     print("{}:{}".format(i, pResGeo.GetGeometryCount()))
            # else:
            #     print(i)

        i += 1
        pFeat = inLayer.GetNextFeature()

    inDataSource.Destroy()
    inClipSource.Destroy()

    end = time.time()
    print("clip操作总共耗时 " + str(end - start) + "\n")


def clip_gdb(input, clip):
    start = time.time()

    driver = ogr.GetDriverByName("FileGDB")
    inDataSource = driver.Open(input, 0)
    inLayer = inDataSource.GetLayerByName("T2019一张图拼合")

    print(inLayer.GetFeatureCount())

    ## Clip
    inClipSource = driver.Open(clip, 0)
    inClipLayer = inClipSource.GetLayerByName("建设用地布局方案1100")

    i = 0
    pFeat = inLayer.GetNextFeature()
    while pFeat is not None:
        pGeom = pFeat.GetGeometryRef()

        # inClipLayer.ResetReading()
        inClipLayer.SetSpatialFilter(pGeom)
        # pClipGeo = pGeom.Intersection(poClipGeo)
        multi = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in inClipLayer:
            pGeo = feature.GetGeometryRef()
            # pResGeo = pGeom.Intersection(pGeo)
            multi.AddGeometry(pGeo)

        pGeo = multi.UnionCascaded()
        if pGeo is not None:
            pResGeo = pGeom.Intersection(pGeo)
            # if pResGeo is not None:
            #     print("{}:{}".format(i, pResGeo.GetGeometryCount()))
            # else:
            #     print(i)

        i += 1
        pFeat = inLayer.GetNextFeature()

    # print(outLayer.GetFeatureCount())

    # try:
    #     with open("erase.cpg", "r+") as f:
    #         f.seek(0)
    #         f.truncate() #清空文件
    #         f.write('ISO-8859-1')
    # finally:
    #     if f:
    #         f.close()

    inDataSource.Destroy()
    inClipSource.Destroy()
    # outDataSource.Destroy()

    end = time.time()
    print("clip操作总共耗时 " + str(end - start) + "\n")


def clip_gpkg(input, clip):
    start = time.time()

    driver = ogr.GetDriverByName("GPKG")
    inDataSource = driver.Open(input, 0)
    inLayer = inDataSource.GetLayerByName("一张图")

    print(inLayer.GetFeatureCount())

    ## Clip
    inClipSource = driver.Open(clip, 0)
    inClipLayer = inClipSource.GetLayerByName("建设用地")

    outdriver = ogr.GetDriverByName('FileGDB')
    output_path = "res/res.gdb"
    if os.path.exists(output_path):
        outDataSource = outdriver.Open(output_path, 1)
        logging.info("文件数据库已存在，在已有数据库基础上创建图层.")
    else:
        outDataSource = outdriver.CreateDataSource(output_path)

    outLayer = outDataSource.CreateLayer("clip", geom_type=ogr.wkbPolygon)

    # pUnionGeo = loadGeometry(inClipLayer)

    i = 0
    pFeat = inLayer.GetNextFeature()
    while pFeat is not None:
        pGeom = pFeat.GetGeometryRef()

        # inClipLayer.ResetReading()
        inClipLayer.SetSpatialFilter(pGeom)
        # pClipGeo = pGeom.Intersection(poClipGeo)
        multi = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in inClipLayer:
            # pGeo = feature.GetGeometryRef()
            # pResGeo = pUnionGeo.Intersection(pGeo)
            # if pResGeo is not None:
            #     print("{}:{}".format(i, pResGeo.GetGeometryCount()))
            # else:
            #     print(i)
            pGeo = feature.GetGeometryRef()
            if pGeo.GetGeometryType() == ogr.wkbMultiPolygon:
                multi.AddGeometry(ogr.ForceToPolygon(pGeo))
            else:
                multi.AddGeometry(pGeo)

        pGeo = multi.UnionCascaded()
        if pGeo is not None:
            pResGeo = pGeom.Intersection(pGeo)
            if pResGeo is not None:
                print("{}:{}".format(i, pResGeo.GetGeometryCount()))
            else:
                print(i)

        pFeat = inLayer.GetNextFeature()
        i += 1

    inDataSource.Destroy()
    inClipSource.Destroy()

    end = time.time()
    print("clip操作总共耗时 " + str(end - start) + "\n")


def loadGeometry(poLyr):
    poGeom = None
    poFeat = poLyr.GetNextFeature()
    ifeaCount = 0
    while poFeat is not None:
        posrcGeom = poFeat.GetGeometryRef()
        posrcGeom = ogr.ForceToPolygon(posrcGeom)
        if ifeaCount == 0:
            pResGeo = posrcGeom.Clone()

        if ifeaCount == 3:
            print("error")

        if posrcGeom is not None:
            eType = wkbFlatten(posrcGeom.GetGeometryType())

            # if poGeom is None:
            #     poGeom = ogr.Geometry(ogr.wkbMultiPolygon)

            if eType == ogr.wkbPolygon:
                # poGeom.AddGeometry(posrcGeom)
                pResGeo = pResGeo.Union(posrcGeom)
            elif eType == ogr.wkbMultiPolygon:
                if posrcGeom is not None:
                    for iGeom in range(posrcGeom.GetGeometryCount()):
                        # poGeom.AddGeometry(posrcGeom.GetGeometryRef(iGeom))
                        pResGeo = pResGeo.Union(posrcGeom)
            else:
                print("ERROR: Geometry not of polygon type.")
                return None

        print(ifeaCount)
        poFeat = poLyr.GetNextFeature()
        ifeaCount += 1

    # pGeo = poGeom.UnionCascaded()
    return ogr.ForceToPolygon(pResGeo)


def wkbFlatten(x):
    return x & (~ogr.wkb25DBit)

def clip(input, clip):
    start = time.time()

    driverName = "GPKG"
    driver = ogr.GetDriverByName(driverName)
    inDataSource = driver.Open(input, 0)
    inLayer = inDataSource.GetLayerByName("一张图")

    print(inLayer.GetFeatureCount())
    ## Clip
    inClipSource = driver.Open(clip, 0)
    inClipLayer = inClipSource.GetLayerByName("建设用地")
    print(inClipLayer.GetFeatureCount())

    outdriver = ogr.GetDriverByName('FileGDB')
    output_path = "res/res.gdb"
    if os.path.exists(output_path):
        outDataSource = outdriver.Open(output_path, 1)
        logging.info("文件数据库已存在，在已有数据库基础上创建图层.")
    else:
        outDataSource = outdriver.CreateDataSource(output_path)

    outLayer = outDataSource.CreateLayer("clip", geom_type=ogr.wkbPolygon)

    ogr.Layer.Clip(inLayer, inClipLayer, outLayer, options=['SKIP_FAILURES=YES'])
    print(outLayer.GetFeatureCount())

    inDataSource.Destroy()
    inClipSource.Destroy()
    outDataSource.Destroy()

    end = time.time()
    print("clip操作总共耗时 " + str(end - start) + "\n")


def erase(input, erase):
    start = time.time()

    driverName = "ESRI Shapefile"
    driver = ogr.GetDriverByName(driverName)
    inDataSource = driver.Open(input, 0)
    inLayer = inDataSource.GetLayer()

    print(inLayer.GetFeatureCount())
    ## Clip
    inClipSource = driver.Open(erase, 0)
    inClipLayer = inClipSource.GetLayer()
    print(inClipLayer.GetFeatureCount())

    outdriver = ogr.GetDriverByName('FileGDB')
    output_path = "res/res.gdb"
    if os.path.exists(output_path):
        outDataSource = outdriver.Open(output_path, 1)
        logging.info("文件数据库已存在，在已有数据库基础上创建图层.")
    else:
        outDataSource = outdriver.CreateDataSource(output_path)

    outLayer = outDataSource.CreateLayer("erase", geom_type=ogr.wkbPolygon)

    ogr.Layer.Erase(inLayer, inClipLayer, outLayer, options=['SKIP_FAILURES=YES'])
    print(outLayer.GetFeatureCount())

    try:
        with open("erase.cpg", "r+") as f:
            f.seek(0)
            f.truncate() #清空文件
            f.write('ISO-8859-1')
    finally:
        if f:
            f.close()

    inDataSource.Destroy()
    inClipSource.Destroy()
    outDataSource.Destroy()

    end = time.time()
    print("erase操作总共耗时 " + str(end - start) + "\n")


if __name__ == '__main__':
    # ogr.UseExceptions()
    gdal.SetConfigOption('CPL_LOG', 'NUL')
    main()