# -*- coding: gbk -*-

import arcpy
import os
import csv
import codecs
import sys
import random

reload(sys)
sys.setdefaultencoding('utf8')

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "�ռ�ģ��"
        self.alias = "SpaceSim"

        # List of tool classes associated with this toolbox
        self.tools = [GenerateBaseMap]


class GenerateBaseMap(object):
    output_ws_name = "res.gdb"
    dir_name = os.path.dirname(os.path.abspath(__file__))
    output_path = dir_name + os.path.sep + output_ws_name

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "GenerateBaseMap"
        self.description = "���ڽ����õغͷ���ͼ�����������õص�ͼ����."
        self.canRunInBackground = False

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
                parameters[1].setErrorMessage("����ͼ��ͼ��ȱ��MAINCODE�ֶ�")
                return
            if not FieldExist(statutory, "floor_area"):
                parameters[1].setErrorMessage("����ͼ��ͼ��ȱ���ݻ����ֶ�floor_area")
                return
            if not FieldExist(statutory, "remark"):
                parameters[1].setErrorMessage("����ͼ��ͼ��ȱ�ٱ�ע�ֶ�remark")
                return

        if parameters[5].value > 0:
            admin_region = parameters[5].valueAsText
            if not FieldExist(admin_region, "QNAME"):
                parameters[5].setErrorMessage("������ͼ��ȱ�������ֶ�QNAME")
                return

        if parameters[6].value > 0:
            supplement = parameters[6].valueAsText
            if not FieldExist(supplement, "����"):
                parameters[6].setErrorMessage("�˹�����ͼ��ȱ�������ֶ�")
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
        arcpy.Erase_analysis(construction, statutory, "A2")

        messages.addMessage("���Ĳ�:����ԭ�ܹ�P��A2���ص�����A3...")
        arcpy.Clip_analysis(planning, "A2", "A3") # self.output_path + os.path.sep + "A2"
        UpdateField("A3", source_field, '"�ܹ�"')
        #
        messages.addMessage("���岽:����A2����ԭ�ܹ�P���A4...")
        arcpy.Erase_analysis("A2", planning, "A4")
        UpdateField("A4", source_field, '"����"')
        arcpy.SpatialJoin_analysis("A4", supplement, "A4_join",
                                   match_option="CLOSEST", search_radius=500)
        arcpy.MakeFeatureLayer_management("A4_join", "A4_join_lyr")
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
        arcpy.Merge_management(["A1", "A3", "A4"], "A5", fieldMappings)

        messages.addMessage("���߲�:�����ֶβ�������ͼ��baseMap...")
        arcpy.SpatialJoin_analysis("A5", admin_region, r"in_memory\baseMap",  # r"in_memory\baseMap"
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

#############################################################################
#  ��������
#############################################################################
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


def LaunderName(output_path, name):
    arcpy.env.workspace = output_path
    if arcpy.Exists(name):
        name = name + "_1"

    if not arcpy.Exists(name):
        return name
    else:
        LaunderName(output_path, name)
