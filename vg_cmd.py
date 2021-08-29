# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_cmd.py
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
__title__ = "VariantGenerator"
__author__ = "David Vachulka"
__url__ = "https://github.com/archdvx/VariantGenerator"
__date__ = "2021.03.13"
__version__ = "1.00"
version = 1.00

from PySide import QtCore, QtGui
import os
import FreeCAD
from vg_bodygenerator import BodyGenerator
from vg_partgenerator import PartGenerator

if FreeCAD.GuiUp:
    from FreeCAD import Gui


def QT_TRANSLATE_NOOP(scope, text):
    return text


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'icons')
keepToolbar = False


class BodyCommandClass(object):
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'body.svg'),
                'MenuText': QT_TRANSLATE_NOOP("BodyGenerator", "Generate files from &bodies"),
                'ToolTip': QT_TRANSLATE_NOOP("BodyGenerator",
                                             "Generate files from bodies by variables from CSV file")}

    def Activated(self):
        if self.has_some_body():
            dlg = BodyGenerator()
            dlg.exec_()
        else:
            QtGui.QMessageBox.information(
                QtGui.QApplication.activeWindow(), translate("VG", "Information"),
                translate("VG", "Document hasn't any body"))
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def has_some_body(self):
        objs = FreeCAD.ActiveDocument.Objects
        for obj in objs:
            if obj.TypeId == "PartDesign::Body":
                return True
        return False


class PartCommandClass(object):
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath, 'part.svg'),
                'MenuText': QT_TRANSLATE_NOOP("PartGenerator", "Generate files from &parts"),
                'ToolTip': QT_TRANSLATE_NOOP("PartGenerator",
                                             "Generate files from parts by variables from CSV file")}

    def Activated(self):
        if self.has_some_part():
            dlg = PartGenerator()
            dlg.exec_()
        else:
            QtGui.QMessageBox.information(
                QtGui.QApplication.activeWindow(), translate("VG", "Information"),
                translate("VG", "Document hasn't any part"))
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def has_some_part(self):
        objs = FreeCAD.ActiveDocument.Objects
        for obj in objs:
            if obj.TypeId == "App::Part":
                return True
        return False


def initialize():
    if FreeCAD.GuiUp:
        Gui.addCommand("BodyGenerator", BodyCommandClass())
        Gui.addCommand("PartGenerator", PartCommandClass())
        Gui.updateLocale()


initialize()
