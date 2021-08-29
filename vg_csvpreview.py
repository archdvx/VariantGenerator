# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_csvpreview.py
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


def QT_TRANSLATE_NOOP(scope, text):
    return text


# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class CsvPreview(QtGui.QDialog):

    def __init__(self, csvpath, parent=None):
        super(CsvPreview, self).__init__(parent)
        self.csvpath = csvpath

        self.text = QtGui.QTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        if os.path.isfile(self.csvpath):
            with open(self.csvpath) as f:
                content = f.read().splitlines()
                for line in content:
                    self.text.append(line)
        self.text.moveCursor(QtGui.QTextCursor.Start)
        self.text.ensureCursorVisible()

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.text)

        self.setMinimumWidth(550)
        self.setMinimumHeight(400)
        self.setWindowTitle(translate("VG", "Preview CSV"))
