# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_generator.py
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
import os
import csv
import _csv
import FreeCAD
from vg_assignment import AssignmentEdit
from vg_csvpreview import CsvPreview
from vg_lib import is_dir_writable, make_assignment

if FreeCAD.GuiUp:
    from FreeCAD import Gui


def QT_TRANSLATE_NOOP(scope, text):
    return text


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


def some_to_assignment(togenerate):
    objs = FreeCAD.ActiveDocument.Objects
    if togenerate == 1:
        for obj in objs:
            if obj.TypeId == "PartDesign::Body" and len(obj.Group):
                return True
    else:
        for obj in objs:
            if obj.TypeId == "App::Part" and len(obj.Group):
                return True
    return False


# togenerate == 1 -> PartDesign::Body
#               2 -> App::Part
class Generator(QtGui.QDialog):

    def __init__(self, togenerate, parent=None):
        super(Generator, self).__init__(parent)

        self.togenerate = togenerate
        self.variables = []
        self.freecad = ""
        self.csv = ""
        self.output = ""
        self.spreadsheetloaded = False

        self.grid = QtGui.QGridLayout(self)
        i = 0

        self.grid.addWidget(QtGui.QLabel(translate("VG", "CSV file:")), i, 0)
        self.csvpath = QtGui.QLabel("")
        self.grid.addWidget(self.csvpath, i, 1)
        self.csvselect = QtGui.QToolButton()
        self.csvselect.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.csvselect.setText("...")
        self.csvselect.setToolTip(translate("VG", "Select CSV file"))
        self.csvselect.clicked.connect(self.csv_select)
        self.grid.addWidget(self.csvselect, i, 2)
        i += 1

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Output directory:")), i, 0)
        self.outputpath = QtGui.QLabel("")
        self.grid.addWidget(self.outputpath, i, 1)
        self.outputselect = QtGui.QToolButton()
        self.outputselect.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.outputselect.setText("...")
        self.outputselect.setToolTip(translate("VG", "Select Output directory"))
        self.outputselect.clicked.connect(self.output_select)
        self.grid.addWidget(self.outputselect, i, 2)
        i += 1

        self.csvpreview = QtGui.QToolButton()
        self.csvpreview.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.csvpreview.setText(translate("VG", "&Preview CSV"))
        self.csvpreview.clicked.connect(self.csv_preview)
        self.grid.addWidget(
            self.csvpreview, i, 1,
            1, 1,
            QtCore.Qt.AlignCenter)
        i += 1

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Variable used to\nfile name:")), i, 0)
        self.fname = QtGui.QComboBox()
        self.fname.setEnabled(False)
        self.grid.addWidget(self.fname, i, 1)
        self.fnameselect = QtGui.QToolButton()
        self.fnameselect.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.fnameselect.setText(translate("VG", "Load variables from &CSV"))
        self.fnameselect.clicked.connect(self.load_variables)
        self.grid.addWidget(self.fnameselect, i, 2)
        i += 1

        if self.togenerate == 1:
            self.grid.addWidget(QtGui.QLabel(translate("VG", "Bodies to generate:")), i, 0)
        else:
            self.grid.addWidget(QtGui.QLabel(translate("VG", "Parts to generate:")), i, 0)
        self.list = QtGui.QListWidget()
        self.list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.list.setMaximumHeight(200)
        objs = FreeCAD.ActiveDocument.Objects
        if self.togenerate == 1:
            for obj in objs:
                if obj.TypeId == "PartDesign::Body":
                    self.list.addItem(obj.Label)
        else:
            for obj in objs:
                if obj.TypeId == "App::Part":
                    self.list.addItem(obj.Label)
        self.grid.addWidget(self.list, i, 1)
        i += 1

        self.cells = QtGui.QTreeWidget()
        self.cells.setHeaderLabels([translate("VG", "CSV Variable"), translate("VG", "FreeCAD Attribute")])
        self.cells.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.cells.setAlternatingRowColors(True)
        self.cells.setRootIsDecorated(False)
        self.cells.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.grid.addWidget(self.cells, i, 0, 6, 2)
        self.addrow = QtGui.QToolButton()
        self.addrow.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.addrow.setText(translate("VG", "&Add"))
        self.addrow.clicked.connect(self.add_row)
        self.grid.addWidget(self.addrow, i, 2)
        self.modifyrow = QtGui.QToolButton()
        self.modifyrow.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.modifyrow.setText(translate("VG", "&Modify"))
        self.modifyrow.clicked.connect(self.modify_row)
        self.modifyrow.setEnabled(False)
        self.grid.addWidget(self.modifyrow, i + 1, 2)
        self.deleterow = QtGui.QToolButton()
        self.deleterow.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.deleterow.setText(translate("VG", "&Delete"))
        self.deleterow.clicked.connect(self.delete_row)
        self.deleterow.setEnabled(False)
        self.grid.addWidget(self.deleterow, i + 2, 2)
        self.clearcells = QtGui.QToolButton()
        self.clearcells.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.clearcells.setText(translate("VG", "&Clear all"))
        self.clearcells.clicked.connect(self.clear_cells)
        self.clearcells.setEnabled(False)
        self.grid.addWidget(self.clearcells, i + 3, 2)
        i += 7

        self.grid.addWidget(QtGui.QLabel(translate("VG", "Output file format:")), i, 0)
        self.format = QtGui.QComboBox()
        self.format.addItem(translate("VG", "STEP with colors (*.stp)"), ".stp")
        self.format.addItem(translate("VG", "IGES format (*.iges)"), ".iges")
        self.format.addItem(translate("VG", "VRML V2.0 (*.wrl)"), ".wrl")
        self.format.addItem(translate("VG", "STL Mesh (*.stl)"), ".stl")
        self.format.addItem(translate("VG", "Alias Mesh (*.obj)"), ".obj")
        if len(FreeCAD.getExportType("iv")):
            self.format.addItem(translate("VG", "Open Inventor (*.iv)"), ".iv")
        if len(FreeCAD.getExportType("x3d")):
            self.format.addItem(translate("VG", "X3D Extensible 3D (*.x3d)"), ".x3d")
        if len(FreeCAD.getExportType("json")):
            self.format.addItem(translate("VG", "JavaScript Object Notation (*.json)"), ".json")
        self.format.addItem(translate("VG", "WebGL file (*.html)"), ".html")
        if len(FreeCAD.getExportType("xhtml")):
            self.format.addItem(translate("VG", "WebGL/X3D (*.xhtml)"), ".xhtml")
        self.format.addItem(translate("VG", "Portable Document Format (*.pdf)"), ".pdf")
        self.grid.addWidget(self.format, i, 1)
        i += 1

        self.hbox = QtGui.QHBoxLayout()
        self.load = QtGui.QPushButton(translate("VG", "&Load settings"))
        self.load.clicked.connect(self.load_settings)
        self.save = QtGui.QPushButton(translate("VG", "&Save settings"))
        self.save.clicked.connect(self.save_settings)
        self.hbox.addWidget(self.load)
        self.hbox.addWidget(self.save)
        self.grid.addLayout(self.hbox, i, 0, 1, 3, QtCore.Qt.AlignCenter)
        i += 1

        self.start = QtGui.QPushButton(translate("VG", "&Generate"))
        self.start.setStyleSheet("font: bold")
        self.start.clicked.connect(self.generate_files)
        self.grid.addWidget(
            self.start, i, 1,
            1, 1,
            QtCore.Qt.AlignCenter)
        i += 1

        self.progress = QtGui.QProgressBar()
        self.grid.addWidget(self.progress, i, 0, 1, 3)

        self.mainsizer = QtGui.QVBoxLayout()
        self.mainsizer.addLayout(self.grid)

        self.setLayout(self.mainsizer)

    def start_path(self):
        if not self.csv == '':
            return os.path.dirname(self.csv)
        if not self.output == '':
            return self.output
        return os.path.expanduser('~')

    def load_settings(self):
        dialog = QtGui.QFileDialog.getOpenFileName(
            self,
            translate("VG", "Open settings file"),
            self.start_path(),
            translate("VG", "Settings Files (*.vcg)")
        )
        ini = dialog[0]
        if not os.path.isfile(ini):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "File {0} doesn't exist".format(ini)))
            return
        sts = QtCore.QSettings(ini, QtCore.QSettings.IniFormat)
        sts.beginGroup("BASIC")
        self.csv = os.path.normpath(os.path.join(os.path.dirname(ini), sts.value("csv")))
        if os.path.isfile(self.csv):
            self.csvpath.setText(self.csv)
            self.csvpath.setToolTip(self.csv)
            self.load_variables()
        if self.fname.count() != 0:
            self.fname.setCurrentIndex(self.fname.findText(sts.value("fname")))
        index = self.format.findData(sts.value("ext", ".stp"))
        if index != -1:
            self.format.setCurrentIndex(index)
        else:
            self.format.setCurrentIndex(0)
        self.output = os.path.normpath(os.path.join(os.path.dirname(ini), sts.value("output")))
        self.outputpath.setText(self.output)
        self.outputpath.setToolTip(self.output)
        sts.endGroup()
        sts.beginGroup("BODIES") if self.togenerate == 1 else sts.beginGroup("PARTS")
        count = int(sts.value("count", 0))
        if count > 0:
            if self.togenerate == 1:
                for i in range(count):
                    items = self.list.findItems(sts.value("body" + str(i), "prd"), QtCore.Qt.MatchExactly)
                    for item in items:
                        item.setSelected(True)
            else:
                for i in range(count):
                    items = self.list.findItems(sts.value("part" + str(i), "prd"), QtCore.Qt.MatchExactly)
                    for item in items:
                        item.setSelected(True)
        sts.endGroup()
        sts.beginGroup("ASSIGNMENTS")
        count = int(sts.value("count", 0))
        if count > 0:
            for i in range(count):
                if sts.value("variable" + str(i)) in self.variables:
                    fobj = None
                    for obj in FreeCAD.ActiveDocument.Objects:
                        if obj.Name == sts.value("obj" + str(i)):
                            fobj = obj
                            break
                    if fobj:
                        fproperty = ""
                        if "PartDesign" in fobj.Module and "Body" not in fobj.TypeId and sts.value(
                                "property" + str(i)) in fobj.PropertiesList:
                            fproperty = sts.value("property" + str(i))
                        if "Part::" in fobj.TypeId and sts.value(
                                "property" + str(i)) in fobj.PropertiesList:
                            fproperty = sts.value("property" + str(i))
                        if "Spreadsheet" in obj.Module:
                            for line in obj.cells.Content.splitlines():
                                if "<Cell address=" in line:
                                    idx = line.find("address=\"") + len("address=\"")
                                    idx2 = line.find("\"", idx)
                                    if sts.value("property" + str(i)) == line[idx:idx2]:
                                        fproperty = line[idx:idx2]
                        if "SketchObject" in obj.TypeId:
                            for con in obj.Constraints:
                                if con.Name and con.Driving and con.Name == sts.value("property" + str(i)):
                                    fproperty = con.Name
                        if "FeaturePython" in obj.TypeId and "DynamicData" in obj.PropertiesList and sts.value(
                                "property" + str(i)) in fobj.PropertiesList:
                            fproperty = sts.value("property" + str(i))
                        if fproperty != "":
                            item = QtGui.QTreeWidgetItem([sts.value("variable" + str(i)),
                                                          fobj.Label + "-" + fproperty])
                            item.setData(0, QtCore.Qt.UserRole, {'obj': fobj, 'property': fproperty})
                            self.cells.addTopLevelItem(item)
                            self.cells.setCurrentItem(item)
                            self.modifyrow.setEnabled(True)
                            self.deleterow.setEnabled(True)
                            self.clearcells.setEnabled(True)
        sts.endGroup()
        QtGui.QMessageBox.information(
            self, translate("VG", "Information"),
            translate("VG", "Settings loaded"))

    def save_settings(self):
        if self.csv == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of CSV file is empty"))
            self.csv_select()
            if self.csv == "":
                QtGui.QMessageBox.information(self, translate("VG", "Information"),
                                              translate("VG", "Settings wasn't saved"))
                return
        if self.output == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of Output Directory is empty"))
            self.output_select()
            if self.output == "":
                QtGui.QMessageBox.information(self, translate("VG", "Information"),
                                              translate("VG", "Settings wasn't saved"))
                return
        if not is_dir_writable(self.output):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of Output Directory isn't writable"))
            self.output_select()
            if not is_dir_writable(self.output):
                QtGui.QMessageBox.information(self, translate("VG", "Information"),
                                              translate("VG", "Settings wasn't saved"))
                return
        if self.fname.count() == 0:
            QtGui.QMessageBox.information(
                self, translate("VG", "Information"),
                translate("VG", "Select variable used to file name first"))
            self.load_variables()
            QtGui.QMessageBox.information(self, translate("VG", "Information"),
                                          translate("VG", "Settings wasn't saved"))
            return
        parts = self.list.selectedItems()
        if len(parts) == 0:
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Any body selected") if self.togenerate == 1 else translate("VG", "Any part selected"))
            self.list.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            self.list.setCurrentRow(0)
            QtGui.QMessageBox.information(self, translate("VG", "Information"),
                                          translate("VG", "Settings wasn't saved"))
            return
        dialog = QtGui.QFileDialog.getSaveFileName(
            self,
            translate("VG", "Select settings file"),
            self.start_path(),
            translate("VG", "Settings Files (*.vcg)")
        )
        ini = dialog[0]
        if os.path.splitext(ini)[1] == '':
            ini = ini + ".vcg"
        sts = QtCore.QSettings(ini, QtCore.QSettings.IniFormat)
        for key in sts.allKeys():
            sts.remove(key)
        sts.beginGroup("BASIC")
        sts.setValue("csv", os.path.relpath(self.csv, os.path.dirname(ini)))
        sts.setValue("output", os.path.relpath(self.output, os.path.dirname(ini)))
        sts.setValue("fname", self.fname.currentText())
        sts.setValue("ext", self.format.currentData())
        sts.endGroup()
        sts.beginGroup("BODIES") if self.togenerate == 1 else sts.beginGroup("PARTS")
        i = 0
        sts.setValue("count", len(parts))
        for part in parts:
            sts.setValue("body" + str(i), part.text()) if self.togenerate == 1 \
                else sts.setValue("part" + str(i), part.text())
            i += 1
        sts.endGroup()
        sts.beginGroup("ASSIGNMENTS")
        sts.setValue("count", self.cells.topLevelItemCount())
        for i in range(self.cells.topLevelItemCount()):
            sts.setValue("variable" + str(i), self.cells.topLevelItem(i).text(0))
            sts.setValue("obj" + str(i), self.cells.topLevelItem(i).data(0, QtCore.Qt.UserRole)['obj'].Name)
            sts.setValue("property" + str(i), self.cells.topLevelItem(i).data(0, QtCore.Qt.UserRole)['property'])
        sts.endGroup()
        sts.sync()

    def csv_select(self):
        dialog = QtGui.QFileDialog.getOpenFileName(
            self,
            translate("VG", "Open CSV file"),
            self.start_path(),
            translate("VG", "CSV Files (*.csv)")
        )
        self.csv = dialog[0]
        self.csvpath.setText(self.csv)
        self.csvpath.setToolTip(self.csv)

    def output_select(self):
        self.output = QtGui.QFileDialog.getExistingDirectory(
            self,
            translate("VG", "Output Directory"),
            self.start_path(),
            QtGui.QFileDialog.ShowDirsOnly
            | QtGui.QFileDialog.DontResolveSymlinks)
        self.outputpath.setText(self.output)
        self.outputpath.setToolTip(self.output)

    def csv_preview(self):
        if self.csv == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of CSV file is empty"))
            self.csv_select()
            if self.csv == "":
                return
        if not os.path.isfile(self.csv):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "File {0} doesn't exist".format(self.csv)))
            self.csv_select()
            return
        preview = CsvPreview(
            self.csv,
            self)
        preview.exec_()

    def load_variables(self):
        if self.csv == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of CSV file is empty"))
            self.csv_select()
            if self.csv == "":
                return False
        if not os.path.isfile(self.csv):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "File {0} doesn't exist".format(self.csv)))
            self.csv_select()
            return False
        with open(self.csv) as f:
            try:
                d = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.reader(f, d)
                self.variables = next(reader)
            except _csv.Error:
                QtGui.QMessageBox.critical(
                    self, translate("VG", "Error"),
                    translate("VG", "Error during loading CSV file, problem with delimiter")
                )
                return False
        self.fname.clear()
        for v in self.variables:
            self.fname.addItem(v)
        self.fname.setEnabled(True)
        return True

    def add_row(self):
        if len(self.variables) == 0:
            if not self.load_variables():
                return
        if not some_to_assignment(self.togenerate):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Nothing to assignment"))
            return
        dialog = AssignmentEdit(
            self.variables,
            "",
            "",
            self.togenerate,
            self)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            item = QtGui.QTreeWidgetItem([dialog.get_variable(),
                                          dialog.get_assignment()['obj'].Label + "-" + dialog.get_assignment()[
                                              'property']])
            item.setData(0, QtCore.Qt.UserRole, dialog.get_assignment())
            self.cells.addTopLevelItem(item)
            self.cells.setCurrentItem(item)
            self.modifyrow.setEnabled(True)
            self.deleterow.setEnabled(True)
            self.clearcells.setEnabled(True)

    def modify_row(self):
        dialog = AssignmentEdit(
            self.variables,
            self.cells.currentItem().text(0),
            self.cells.currentItem().data(0, QtCore.Qt.UserRole),
            self.togenerate,
            self)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.cells.currentItem().setText(0, dialog.get_variable())
            self.cells.currentItem().setText(1, dialog.get_assignment()['obj'].Label + "-" + dialog.get_assignment()[
                'property'])
            self.cells.currentItem().setData(0, QtCore.Qt.UserRole, dialog.get_assignment())

    def delete_row(self):
        if QtGui.QMessageBox.question(
                self, translate("VG", "Question"),
                translate("VG", "Really delete assignment {0} -> {1}?".format(self.cells.currentItem().text(0),
                                                                              self.cells.currentItem().text(1)))
        ) == QtGui.QMessageBox.Yes:
            self.cells.takeTopLevelItem(self.cells.indexOfTopLevelItem(self.cells.currentItem()))
        if self.cells.topLevelItemCount() < 1:
            self.modifyrow.setEnabled(False)
            self.deleterow.setEnabled(False)
            self.clearcells.setEnabled(False)

    def clear_cells(self):
        self.cells.clear()
        self.modifyrow.setEnabled(False)
        self.deleterow.setEnabled(False)
        self.clearcells.setEnabled(False)

    def generate_files(self):
        if self.csv == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of CSV file is empty"))
            self.csv_select()
            if self.csv == "":
                return
        if not os.path.isfile(self.csv):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "File {0} doesn't exist".format(self.csv)))
            self.csv_select()
            if self.csv == "":
                return
        if self.output == "":
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of Output Directory is empty"))
            self.output_select()
            if self.output == "":
                return
        if not is_dir_writable(self.output):
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Path of Output Directory isn't writable"))
            self.output_select()
            if not is_dir_writable(self.output):
                return
        if self.fname.count() == 0:
            QtGui.QMessageBox.information(
                self, translate("VG", "Information"),
                translate("VG", "Select variable used to file name first"))
            self.load_variables()
            return
        generate = self.list.selectedItems()
        if len(generate) == 0:
            QtGui.QMessageBox.warning(
                self, translate("VG", "Warning"),
                translate("VG", "Any body selected") if self.togenerate == 1 else translate("VG", "Any part selected"))
            self.list.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            self.list.setCurrentRow(0)
            return
        f = open(self.csv)
        self.progress.setMaximum(sum(1 for _ in f) - 1)
        f.seek(0)
        d = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        r = csv.DictReader(f, dialect=d)
        self.progress.setValue(0)
        __objs__ = []
        doc = FreeCAD.ActiveDocument
        objs = doc.Objects
        if self.togenerate == 1:
            for obj in objs:
                if obj.TypeId == "PartDesign::Body":
                    for item in generate:
                        if obj.Label == item.text():
                            __objs__.append(obj)
        else:
            for obj in objs:
                if obj.TypeId == "App::Part":
                    for item in generate:
                        if obj.Label == item.text():
                            __objs__.append(obj)
        asss = []
        for i in range(self.cells.topLevelItemCount()):
            asss.append({'variable': self.cells.topLevelItem(i).text(0),
                         'obj': self.cells.topLevelItem(i).data(0, QtCore.Qt.UserRole)['obj'],
                         'property': self.cells.topLevelItem(i).data(0, QtCore.Qt.UserRole)['property']})
        ext = self.format.currentData()
        if ext == ".stp":
            import ImportGui
        elif ext == ".iges":
            import Part
        elif ext == ".stl" or ext == ".obj":
            import Mesh
        elif ext == ".wrl" or ext == ".pdf" or ext == ".iv" or ext == ".xhtml" or ext == ".x3d":
            import FreeCADGui
        elif ext == ".json":
            import importJSON
        else:
            import importWebGL
        for row in r:
            FreeCAD.ActiveDocument.openTransaction("row generation")
            for ass in asss:
                make_assignment(row, str(ass['variable']), ass['obj'], ass['property'])
            FreeCAD.ActiveDocument.commitTransaction()
            doc.recompute()
            if ext == ".stp":
                ImportGui.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            elif ext == ".iges":
                Part.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            elif ext == ".stl" or ext == ".obj":
                Mesh.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            elif ext == ".wrl" or ext == ".pdf" or ext == ".iv" or ext == ".xhtml" or ext == ".x3d":
                FreeCADGui.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            elif ext == ".json":
                importJSON.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            else:
                importWebGL.export(__objs__, self.output + "/" + row[self.fname.currentText()] + ext)
            self.progress.setValue(self.progress.value() + 1)
            doc.undo()
        QtGui.QMessageBox.information(
            self, translate("VG", "Information"),
            translate("VG", "Finished"))
        doc.recompute()
        del __objs__
