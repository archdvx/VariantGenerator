# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
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

import os
import vg_locator

vglocatorPath = os.path.dirname(vg_locator.__file__)
vg_icons_path = os.path.join(vglocatorPath, 'icons')

global main_variantgenerator_Icon

main_variantgenerator_Icon = os.path.join(vg_icons_path, 'vg.svg')


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


####################################################################################
# Initialize the workbench
class VariantGeneratorWorkbench(Workbench):
    MenuText = "Variant Generator"
    ToolTip = "Variant Generator workbench"
    Icon = main_variantgenerator_Icon

    def __init__(self):
        pass

    def Initialize(self):
        # This function is executed when FreeCAD starts
        import vg_lib
        FreeCADGui.addLanguagePath(vg_lib.get_language_path())

        def QT_TRANSLATE_NOOP(scope, text):
            return text

        import vg_cmd  # needed files for FreeCAD commands
        self.list = ["BodyGenerator", "PartGenerator"]  # A list of command names created in the line above
        self.appendToolbar("Variant Generator Commands", self.list)
        self.appendMenu("&Variant Generator", self.list)  # creates a new menu

    def Activated(self):
        # This function is executed when the workbench is activated
        return

    def Deactivated(self):
        # This function is executed when the workbench is deactivated
        return

    def ContextMenu(self, recipient):
        # This is executed whenever the user right-clicks on screen
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("Variant Generator", self.list)

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


Gui.addWorkbench(VariantGeneratorWorkbench())
