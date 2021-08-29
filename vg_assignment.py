# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_assignment.py
#
#  Copyright 2021 David Vachulka (archdvx@dxsolutions.org)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
###################################################################################

from PySide import QtCore, QtGui
import FreeCAD

partdesignProperties = [
    "App::PropertyAngle",
    "App::PropertyIntegerConstraint",
    "App::PropertyLength",
    "App::PropertyQuantityConstraint"]

partProperties = [
    "App::PropertyAngle",
    "App::PropertyDistance",
    "App::PropertyInteger",
    "App::PropertyIntegerConstraint",
    "App::PropertyLength",
    "App::PropertyQuantityConstraint"]


def QT_TRANSLATE_NOOP(scope, text):
    return text


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


def property_value_partdesign(obj, prop):
    for expr in obj.ExpressionEngine:
        if prop == expr[0]:
            return expr[1]
    return str(obj.getPropertyByName(prop))


def property_value_sketch(obj, prop):
    for expr in obj.ExpressionEngine:
        if 'Constraints.' + prop == expr[0]:
            return expr[1]
    i = 0
    indexlist = ''
    for con in obj.Constraints:
        if con.Name == prop:
            indexlist = i
            break
        i += 1
    return str(obj.getDatum(indexlist))


class AssignmentEdit(QtGui.QDialog):

    def __init__(self, variables, variable, assignment, togenerate, parent=None):
        super(AssignmentEdit, self).__init__(parent)

        self.togenerate = togenerate

        self.grid = QtGui.QGridLayout()

        self.grid.addWidget(QtGui.QLabel(translate("VG", "CSV Variable")), 0, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItems(variables)
        if len(variable) != 0:
            self.combo.setCurrentIndex(self.combo.findText(variable))
        else:
            self.combo.setCurrentIndex(0)
        self.grid.addWidget(self.combo, 0, 1)

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Assignment")), 1, 0, 1, 2, QtCore.Qt.AlignCenter)

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Object")), 2, 0)
        self.object = QtGui.QComboBox()
        self.fill_object()
        if len(variable) != 0:
            self.object.setCurrentIndex(self.object.findData(assignment['obj']))
        else:
            self.object.setCurrentIndex(0)
        self.object.currentIndexChanged.connect(self.object_changed)
        self.grid.addWidget(self.object, 2, 1)

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Property")), 3, 0)
        self.property = QtGui.QComboBox()
        if len(variable) != 0:
            self.fill_property(assignment['obj'])
            self.property.setCurrentIndex(self.property.findData(assignment['property']))
        else:
            self.fill_property(self.object.itemData(0))
        self.grid.addWidget(self.property, 3, 1)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainsizer = QtGui.QVBoxLayout()
        self.mainsizer.addLayout(self.grid)
        self.mainsizer.addWidget(self.buttonBox)

        self.setLayout(self.mainsizer)
        if len(variable) != 0:
            self.setWindowTitle(translate("VG", "Edit assignment"))
        else:
            self.setWindowTitle(translate("VG", "New assignment"))

    def get_variable(self):
        return self.combo.currentText()

    def get_assignment(self):
        return {'obj': self.object.itemData(self.object.currentIndex()),
                'property': self.property.itemData(self.property.currentIndex())}

    def fill_object(self):
        i = 0
        doc = FreeCAD.ActiveDocument
        objs = doc.Objects
        for obj in objs:
            if self.togenerate == 1:
                if obj.TypeId == "PartDesign::Body" and len(obj.Group):
                    for chobj in obj.Group:
                        for p in chobj.PropertiesList:
                            if "Part::" in chobj.TypeId:
                                if chobj.getTypeIdOfProperty(p) in partProperties:
                                    self.object.addItem(chobj.Label + " (" + chobj.Name + ")", chobj)
                                    break
                            else:
                                if chobj.getTypeIdOfProperty(p) in partdesignProperties:
                                    self.object.addItem(chobj.Label + " (" + chobj.TypeId.partition("::")[2] + ")", chobj)
                                    break
            else:
                if obj.TypeId == "App::Part" and len(obj.Group):
                    for chobj in obj.Group:
                        for p in chobj.PropertiesList:
                            if "Part::" in chobj.TypeId:
                                if chobj.getTypeIdOfProperty(p) in partProperties:
                                    self.object.addItem(chobj.Label + " (" + chobj.Name + ")", chobj)
                                    break
                            else:
                                if chobj.getTypeIdOfProperty(p) in partdesignProperties:
                                    self.object.addItem(chobj.Label + " (" + chobj.TypeId.partition("::")[2] + ")", chobj)
                                    break
            if "Spreadsheet" in obj.Module:
                for line in obj.cells.Content.splitlines():
                    if line.find("address=\"") > 0:
                        self.object.insertItem(i, obj.Label + " (" + obj.TypeId.partition("::")[0] + ")", obj)
                        i += 1
                        break
            if "SketchObject" in obj.TypeId:
                for con in obj.Constraints:
                    if con.Name and con.Driving:
                        self.object.addItem(obj.Label + " (Sketch)", obj)
            if "FeaturePython" in obj.TypeId and "DynamicData" in obj.PropertiesList:
                for p in obj.PropertiesList:
                    if obj.getTypeIdOfProperty(p) in partdesignProperties:
                        self.object.insertItem(i, obj.Label + " (DynamicData)", obj)
                        i += 1
                        break

    def fill_property(self, obj):
        self.property.clear()
        if "PartDesign" in obj.Module and "Body" not in obj.TypeId:
            for p in obj.PropertiesList:
                if obj.getTypeIdOfProperty(p) in partdesignProperties:
                    if obj.getDocumentationOfProperty(p):
                        self.property.addItem(
                            p + " (" + obj.getDocumentationOfProperty(p) + ")" + ", " + translate("VG", "Value: ") +
                            property_value_partdesign(obj, p), p
                        )
                    else:
                        self.property.addItem(p + ", " + translate("VG", "Value: ") + property_value_partdesign(obj, p), p)
        if "Part::" in obj.TypeId:
            for p in obj.PropertiesList:
                if obj.getTypeIdOfProperty(p) in partProperties:
                    if obj.getDocumentationOfProperty(p):
                        self.property.addItem(
                            p + " (" + obj.getDocumentationOfProperty(p) + ")" + ", " + translate("VG", "Value: ") +
                            property_value_partdesign(obj, p), p
                        )
                    else:
                        self.property.addItem(p + ", " + translate("VG", "Value: ") + property_value_partdesign(obj, p), p)
        if "Spreadsheet" in obj.Module:
            for line in obj.cells.Content.splitlines():
                if "<Cell address=" in line:
                    idx = line.find("address=\"") + len("address=\"")
                    idx2 = line.find("\"", idx)
                    name = line[idx:idx2]
                    idx = line.find("content=\"") + len("content=\"")
                    idx2 = line.find("\"", idx)
                    value = line[idx:idx2]
                    self.property.addItem(name + ", " + translate("VG", "Value: ") + value, name)
        if "SketchObject" in obj.TypeId:
            for con in obj.Constraints:
                if con.Name and con.Driving:
                    self.property.addItem(
                        con.Name + " " + translate("VG", "(Constraint)") + ", " + translate("VG", "Value: ") +
                        property_value_sketch(obj, con.Name),
                        con.Name
                    )
        if "FeaturePython" in obj.TypeId and "DynamicData" in obj.PropertiesList:
            for p in obj.PropertiesList:
                if obj.getTypeIdOfProperty(p) in partdesignProperties:
                    if obj.getDocumentationOfProperty(p):
                        self.property.addItem(
                            p + " (" + obj.getDocumentationOfProperty(p) + ")" + ", " + translate("VG", "Value: ") +
                            property_value_partdesign(obj, p), p
                        )
                    else:
                        self.property.addItem(p + ", " + translate("VG", "Value: ") + property_value_partdesign(obj, p), p)

    def object_changed(self, index):
        self.fill_property(self.object.itemData(index))
