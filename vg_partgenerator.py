# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_partgenerator.py
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
import FreeCAD
from vg_generator import Generator

if FreeCAD.GuiUp:
    from FreeCAD import Gui


def QT_TRANSLATE_NOOP(scope, text):
    return text


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


def some_to_assignment():
    objs = FreeCAD.ActiveDocument.Objects
    for obj in objs:
        if obj.TypeId == "App::Part" and len(obj.Group):
            return True
    return False


class PartGenerator(Generator):
    def __init__(self):
        super(PartGenerator, self).__init__(2)

        self.setWindowTitle(translate("VG", "Part variant generator"))

