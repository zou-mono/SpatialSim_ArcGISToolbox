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

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "�ռ�ģ��"
        self.alias = "SpaceSim"

        # List of tool classes associated with this toolbox
        self.tools = [GenerateBaseMap, BuildingStat]


class GenerateBaseMap(object):
    output_ws_name = "res.gdb"
    dir_name = os.path.dirname(os.path.abspath(__file__))
    output_path = dir_name + os.path.sep + output_ws_name

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate BaseMap"
        self.description = "���ڽ����õغͷ���ͼ�����������õص�ͼ����."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        # ���뽨���õ�ͼ��
        param0 = arcpy.Parameter(
            displayName="���뽨���õ�ͼ��",
            name="construction",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # ���뷨��ͼ��ͼ��
        param1 = arcpy.Parameter(
            displayName="���뷨��ͼ��ͼ��",
            name="statutory",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # ����ԭ�ܹ��õط���ͼ��
        param2 = arcpy.Parameter(
            displayName="����ԭ�ܹ��õط���ͼ��",
            name="planning",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # �����ܹ��õ��ֶ�
        param3 = arcpy.Parameter(
            displayName="�ܹ�ͼ���õ������ֶ�",
            name="land_code",
            datatype="Field",
            parameterType="Required",
            direction="input"
        )
        param3.parameterDependencies = [param2.name]

        # ����maincode���ձ��ļ�
        param4 = arcpy.Parameter(
            displayName="����ͼ��MAINCODE��������ձ��ļ�",
            name="maincode_table",
            datatype="DETable",
            parameterType="Required",
            direction="input"
        )

        # ����������ͼ��
        param5 = arcpy.Parameter(
            displayName="�����������߽�ͼ��",
            name="admin_region",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # �˹�����ģ��ͼ��
        param6 = arcpy.Parameter(
            displayName="�����˹�����ģ��ͼ��",
            name="supplement",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # ���
        output = arcpy.Parameter(
            displayName="���·��",
            name="output",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="output"
        )
        output.value = self.output_path

        params = [param0, param1, param2, param3, param4, param5, param6, output]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[1].value > 0:
            statutory = parameters[1].valueAsText
            if not FieldExist(statutory, "maincode"):
                parameters[1].setErrorMessage("ȱ��MAINCODE�ֶ�")
                return
            if not FieldExist(statutory, "floor_area"):
                parameters[1].setErrorMessage("ȱ���ݻ����ֶ�floor_area")
                return
            if not FieldExist(statutory, "remark"):
                parameters[1].setErrorMessage("ȱ�ٱ�ע�ֶ�remark")
                return

        if parameters[5].value > 0:
            admin_region = parameters[5].valueAsText
            if not FieldExist(admin_region, "QNAME"):
                parameters[5].setErrorMessage("ȱ�������ֶ�QNAME")
                return

        if parameters[6].value > 0:
            supplement = parameters[6].valueAsText
            if not FieldExist(supplement, "����"):
                parameters[6].setErrorMessage("ȱ�������ֶ�")
                return

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        construction = parameters[0].valueAsText
        statutory = parameters[1].valueAsText
        planning = parameters[2].valueAsText
        planning_maincode_field = parameters[3].valueAsText
        maincode_table = parameters[4].valueAsText
        admin_region = parameters[5].valueAsText
        supplement = parameters[6].valueAsText
        output = parameters[7].valueAsText

        source_field = "��Դ"
        status_field = "״̬"
        maincode_field = "����"
        FAR_field = "�ݻ���"
        admin_region_field = "������"

        if not arcpy.Exists(output):
            arcpy.CreateFileGDB_management(self.dir_name, self.output_ws_name)
        arcpy.env.workspace = output

        messages.addMessage("��һ��:����ͼ���ֶ�����...")
        # ͼ��ͼ������״̬�ֶΣ�remark�ֶ��а�������״�����ߡ����������ֵ�Ҫ����д����״������
        if not FieldExist(statutory, status_field):
            arcpy.AddField_management(statutory, status_field, "TEXT", field_length=20)
        with arcpy.da.UpdateCursor(statutory, field_names=["remark", status_field],
                                   where_clause="remark LIKE '%��״%' or remark LIKE '%����%'") as cursor:
            for row in cursor:
                row[1] = "��״����"
                cursor.updateRow(row)

        # ����ͼ��ͼ�������ֶ�
        if not FieldExist(statutory, maincode_field):
            arcpy.AddField_management(statutory, maincode_field, "TEXT", field_length=20)
        maincodeDic = maincodeTbl(maincode_table)
        with arcpy.da.UpdateCursor(statutory, field_names=["maincode", "����"]) as cursor:
            for row in cursor:
                row[1] = maincodeDic[row[0]]
                cursor.updateRow(row)

        # ����ͼ���ݻ����ֶ�
        if not FieldExist(statutory, FAR_field):
            arcpy.AddField_management(statutory, FAR_field, "TEXT", field_is_nullable="NON_NULLABLE", field_length=50)
        with arcpy.da.UpdateCursor(statutory, field_names=["floor_area", "�ݻ���"]) as cursor:
            for row in cursor:
                if is_float(row[0]):
                    row[1] = float(row[0])
                else:
                    row[1] = 0
                cursor.updateRow(row)

        # �ܹ�ͼ�����������ֶ�
        UpdateField(planning, maincode_field, '!{}!'.format(planning_maincode_field.encode("gbk")))

        # �����������ֶ�
        if not FieldExist(statutory, admin_region_field):
            arcpy.AddField_management(statutory, admin_region_field, "TEXT", field_is_nullable="NON_NULLABLE", field_length=20)
        # UpdateField(statutory, admin_region_field, "")

        messages.addMessage("�ڶ���:���㽨���õط���C�ͷ���ͼ��S���ص�����A1...")
        arcpy.env.workspace = output
        arcpy.Clip_analysis(statutory, construction, "A1")
        UpdateField("A1", source_field, '"����ͼ��"')

        messages.addMessage("������:���㽨���õط���C���ҷ���ͼ��S��Ĳ���A2...")
        arcpy.Erase_analysis(construction, statutory, r"in_memory\A2")

        messages.addMessage("���Ĳ�:����ԭ�ܹ�P��A2���ص�����A3...")
        arcpy.Clip_analysis(planning, r"in_memory\A2", "A3") # self.output_path + os.path.sep + "A2"
        UpdateField("A3", source_field, '"�ܹ�"')
        #
        messages.addMessage("���岽:����A2����ԭ�ܹ�P���A4...")
        arcpy.Erase_analysis("in_memory\A2", planning, r"in_memory\A4")
        UpdateField(r"in_memory\A4", source_field, '"����"')
        arcpy.SpatialJoin_analysis(r"in_memory\A4", supplement, r"in_memory\A4_join",
                                   match_option="CLOSEST", search_radius=500)
        arcpy.MakeFeatureLayer_management(r"in_memory\A4_join", "A4_join_lyr")
        arcpy.SelectLayerByAttribute_management("A4_join_lyr", "NEW_SELECTION", "����<>'' AND ���� IS NOT NULL")
        arcpy.CopyFeatures_management("A4_join_lyr", r"in_memory\non_empty")

        arcpy.SelectLayerByAttribute_management("A4_join_lyr", "NEW_SELECTION", "����='' or ���� IS NULL")
        arcpy.CopyFeatures_management("A4_join_lyr", r"in_memory\empty")
        values = ["'S'", "'T'"]
        arcpy.CalculateField_management(r"in_memory\empty", maincode_field, random.choice(values), "PYTHON")
        arcpy.Merge_management([r"in_memory\empty", r"in_memory\non_empty"], "A4")

        messages.addMessage("������:�ϲ�A1,A3��A4�����ֵõ�A5...")
        fieldMappings = arcpy.FieldMappings()
        fieldMappings.addTable("A1")
        fieldMappings.addTable("A3")
        fieldMappings.addTable("A4")
        output_fields = []
        A1_fields = arcpy.ListFields("A1")
        for field in A1_fields:
            output_fields.append(field.name)

        for field in fieldMappings.fields:
            if field.name not in output_fields:
                fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(field.name))
        arcpy.Merge_management(["A1", "A3", "A4"], r"in_memory\A5", fieldMappings)

        messages.addMessage("���߲�:�����ֶβ�������ͼ��baseMap...")
        arcpy.SpatialJoin_analysis(r"in_memory\A5", admin_region, r"in_memory\baseMap",  # r"in_memory\baseMap"
                                   match_option="HAVE_THEIR_CENTER_IN")
        arcpy.MakeFeatureLayer_management(r"in_memory\baseMap", "baseMap_lyr")

        arcpy.SelectLayerByAttribute_management("baseMap_lyr", "NEW_SELECTION", "QNAME<>'' and QNAME IS NOT NULL")
        arcpy.CopyFeatures_management("baseMap_lyr", r"in_memory\non_empty")
        arcpy.CalculateField_management(r"in_memory\non_empty", admin_region_field, "!QNAME!", "PYTHON")

        arcpy.SelectLayerByAttribute_management("baseMap_lyr", "NEW_SELECTION", "QNAME='' or QNAME IS NULL")
        # arcpy.CopyFeatures_management("baseMap_lyr", r"in_memory\empty")
        arcpy.SpatialJoin_analysis("baseMap_lyr", admin_region, r"in_memory\empty",
                                   match_option="CLOSEST", search_radius=1000)
        arcpy.CalculateField_management(r"in_memory\empty", admin_region_field, "!QNAME_1!", "PYTHON")

        fieldMappings = arcpy.FieldMappings()
        fieldMappings.addTable(r"in_memory\empty")
        fieldMappings.addTable(r"in_memory\non_empty")
        for field in fieldMappings.fields:
            if field.name not in output_fields:
                fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(field.name))
        arcpy.Merge_management([r"in_memory\empty", r"in_memory\non_empty"], "baseMap", fieldMappings)

        UpdateField(r"in_memory\baseMap", admin_region_field, '!QNAME!')

        return

class BuildingStat(object):
    output_ws_name = "res.gdb"
    dir_name = os.path.dirname(os.path.abspath(__file__))
    output_path = dir_name + os.path.sep + output_ws_name

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Building Type Statistics"
        self.description = "������ͳ��."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # ���뽨�����ղ�����ͼ��
        param0 = arcpy.Parameter(
            displayName="���뽨�����ղ�����ͼ��",
            name="building",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        param1 = arcpy.Parameter(
            displayName="�����õص�ͼ����ͼ��",
            name="baseMap",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="input"
        )

        # ����BLDG_USAGE���ձ��ļ�
        param2 = arcpy.Parameter(
            displayName="����������BLDG_USAGE���õط�����ձ��ļ�",
            name="USAGE_table",
            datatype="DETable",
            parameterType="Required",
            direction="input"
        )

        # ���
        output = arcpy.Parameter(
            displayName="���·��",
            name="output",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="output"
        )
        output.value = self.output_path

        params = [param0, param1, param2, output]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].value > 0:
            building = parameters[0].valueAsText
            desc = arcpy.Describe(building)
            if desc.shapeType != "Polygon":
                parameters[0].setErrorMessage("�������ݼ������ͱ���Ϊpolygon")
                return
            if not FieldExist(building, "BLDG_USAGE"):
                parameters[0].setErrorMessage("ȱ�ٽ����������ֶ�BLDG_USAGE")
            if not FieldExist(building, "FLOOR_AREA"):
                parameters[0].setErrorMessage("ȱ�ٽ�������ֶ�FLOOR_AREA")
            if not FieldTypeExist(building, "FLOOR_AREA", "Double"):
                parameters[0].setErrorMessage("��������ֶ�FLOOR_AREA���ֶ����ͱ���ΪDouble")
            return

        if parameters[1].value > 0:
            baseMap = parameters[1].valueAsText
            desc = arcpy.Describe(baseMap)
            if desc.shapeType != "Polygon":
                parameters[1].setErrorMessage("�������ݼ������ͱ���Ϊpolygon!")
                return

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        building = parameters[0].valueAsText
        baseMap = parameters[1].valueAsText
        usage_table = parameters[2].valueAsText
        output = parameters[3].valueAsText

        usage_field = "�õ�"
        id_field = "landID"
        floor_area_field = "FLOOR_AREA"
        res_table = "buildingStat"

        if not arcpy.Exists(output):
            arcpy.CreateFileGDB_management(self.dir_name, self.output_ws_name)
        arcpy.env.workspace = output

        # arcpy.MakeFeatureLayer_management(building, "building_lyr")
        # with arcpy.da.SearchCursor(baseMap, "SHAPE@") as cursor:
        #     for row in cursor:
        #         # polygons.append(row[0])
        #         polygon = row[0]
        #         # arcpy.CopyFeatures_management(polygons, r'in_memory\geo')
        #         res = arcpy.SelectLayerByLocation_management("building_lyr", "have_their_center_in", polygon)

        messages.addMessage("��һ��:����ͼ����������...")

        polygons = []
        with arcpy.da.SearchCursor(baseMap, "SHAPE@") as cursor:
            for row in cursor:
                polygons.append(row[0])
        arcpy.CopyFeatures_management(polygons, res_table)

        if not FieldExist(building, usage_field):
            arcpy.AddField_management(building, usage_field, "TEXT", field_length=20)
        usageDic = maincodeTbl(usage_table)
        with arcpy.da.UpdateCursor(building, field_names=["BLDG_USAGE", "�õ�"]) as cursor:
            for row in cursor:
                if row[0] in usageDic.keys():
                    row[1] = usageDic[row[0]]
                cursor.updateRow(row)

        if not FieldExist(res_table, id_field):
            arcpy.AddField_management(res_table, id_field, "LONG")
        icount = 0
        with arcpy.da.UpdateCursor(res_table, field_names=[id_field]) as cursor:
            for row in cursor:
                row[0] = icount
                cursor.updateRow(row)
                icount += 1

        messages.addMessage("�ڶ���:ͳ�Ƹ����õؽ�����...")

        fieldMappings = arcpy.FieldMappings()
        fieldMappings.addTable(building)
        fm_id = arcpy.FieldMap()
        fm_id.addInputField(res_table, id_field)
        fieldMappings.addFieldMap(fm_id)
        arcpy.SpatialJoin_analysis(building, res_table, r"in_memory\building_join_baseMap",  # r"in_memory\baseMap"
                                   match_option="HAVE_THEIR_CENTER_IN", field_mapping=fieldMappings)

        idDic = {}  # ���bldg_usage��˳����ֵ�
        lst = []
        for entry in usageDic.values():
            lst.append(entry)
        lst = list(set(lst))
        # arcpy.AddMessage(lst)
        icount = 0
        for entry in lst:
            idDic[entry] = icount
            icount += 1

        # ��һ���������洢ÿ�ཨ�����͵Ľ��������ռ������������˳����idDic
        stat_data = {}
        with arcpy.da.SearchCursor(r"in_memory\building_join_baseMap",
                                   field_names=[id_field, usage_field, floor_area_field, "SHAPE@AREA"]) as cursor:
            for row in cursor:
                if row[0] is None:
                    continue

                if row[1] in idDic.keys():
                    order = idDic[row[1]]
                    # arcpy.AddMessage(str(order))
                    if row[0] not in stat_data.keys():
                        elm_arr = np.zeros(3 * len(idDic) + 1)
                        elm_arr[0] = row[2]
                        elm_arr[order * 3 + 1] = row[2]
                        elm_arr[order * 3 + 2] = row[3]
                        stat_data[row[0]] = elm_arr.copy()
                    else:
                        elm_arr = stat_data[row[0]]
                        elm_arr[0] = elm_arr[0] + row[2]
                        elm_arr[order * 3 + 1] = elm_arr[order * 3 + 1] + row[2]
                        elm_arr[order * 3 + 2] = elm_arr[order * 3 + 2] + row[3]

        # stat_table = createBuidingStatTable(self.output_path, "stat_table", id_field, lst)
        stat_table = createBuidingStatTable("in_memory", "stat_table", id_field, lst)

        with arcpy.da.InsertCursor(stat_table, "*") as cursor:
            icount = 0
            for key, value in stat_data.items():
                if value[0] <= 0:
                    continue
                for i in range(len(lst)):
                    value[3 * i + 3] = value[3 * i + 1] / value[0]
                row = tuple(np.append([icount, key], value))
                icount += 1
                cursor.insertRow(row)

        messages.addMessage("������:�����ֶβ�������ͼ��buildingStat...")
        # arcpy.AddIndex_management(res_table, id_field, "index_id")
        arcpy.JoinField_management(res_table, id_field, stat_table, id_field)

        return

#############################################################################
#  ��������
#############################################################################
def createBuidingStatTable(output, table_name, id_field, typeLst):
    table_path = arcpy.CreateTable_management(output, table_name)
    arcpy.AddField_management(table_path, id_field, "LONG")
    arcpy.AddField_management(table_path, "sum", "DOUBLE")
    for entry in typeLst:
        arcpy.AddField_management(table_path, entry + "_BArea", "DOUBLE", field_alias=entry + "�������")
        arcpy.AddField_management(table_path, entry + "_Area", "DOUBLE", field_alias=entry + "ռ�����")
        arcpy.AddField_management(table_path, entry + "_BProp", "DOUBLE", field_alias=entry + "�����������")
    return table_path


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def maincodeTbl(maincode_table):
    maincodeDic = {}
    result = arcpy.TableToTable_conversion(maincode_table, "in_memory", "table")
    with arcpy.da.SearchCursor(result, "*") as cursor:
        for row in cursor:
            if row[1] != "":
                maincodeDic[row[1].decode("utf8")] = row[2]
            # arcpy.AddMessage(row[1].decode("utf8") + "-" + row[2])
    # with open(maincode_table, "r+") as csvfile:
    #     reader = csv.reader(csvfile)
    #     for row in reader:
    #         maincodeDic[row[0].decode('GBK')] = row[1]
    return maincodeDic


def UpdateField(featureCls, field, expression):
    if not FieldExist(featureCls, field):
        arcpy.AddField_management(featureCls, field, "TEXT", field_length=50)
    arcpy.CalculateField_management(featureCls, field, expression, "PYTHON")


def FieldExist(featureCls, field_name):
    return True if arcpy.ListFields(featureCls, field_name) else False


def FieldTypeExist(featureCls, field_name, field_type):
    fields = arcpy.ListFields(featureCls, field_name)
    return True if fields[0].type == field_type else False


def LaunderName(output_path, name):
    arcpy.env.workspace = output_path
    if arcpy.Exists(name):
        name = name + "_1"

    if not arcpy.Exists(name):
        return name
    else:
        LaunderName(output_path, name)
