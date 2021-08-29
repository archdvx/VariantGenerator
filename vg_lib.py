# -*- coding: utf-8 -*-
###################################################################################
#
#  vg_lib.py
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


def get_language_path():
    return os.path.join(os.path.dirname(__file__), "translations")


def is_dir_writable(path):
    # return os.access(path, os.W_OK | os.X_OK)
    try:
        tmp_prefix = "write_tester"
        count = 0
        filename = os.path.join(path, tmp_prefix)
        while os.path.exists(filename):
            filename = "{}.{}".format(os.path.join(path, tmp_prefix),count)
            count = count + 1
        f = open(filename, "w")
        f.close()
        os.remove(filename)
        return True
    except Exception as e:
        #print "{}".format(e)
        return False


def make_assignment(row, variable, obj, prop):
    if "SketchObject" in obj.TypeId:
        for expr in obj.ExpressionEngine:
            if 'Constraints.' + prop == expr[0]:
                obj.setExpression('Constraints.' + prop, None)
                break
        i = 0
        indexlist = ''
        for con in obj.Constraints:
            if con.Name == prop:
                indexlist = i
                break
            i += 1
        obj.setDatum(indexlist, float(row[variable]))
        return
    if "FeaturePython" in obj.TypeId and "DynamicData" in obj.PropertiesList:
        for expr in obj.ExpressionEngine:
            if prop == expr[0]:
                obj.setExpression(prop, None)
                break
        for p in obj.PropertiesList:
            if p == prop:
                setattr(obj, p, row[variable])
                break
        return
    if "PartDesign" in obj.Module and "Body" not in obj.TypeId:
        for expr in obj.ExpressionEngine:
            if prop == expr[0]:
                obj.setExpression(prop, None)
                obj.recompute()
                break
        for p in obj.PropertiesList:
            if p == prop:
                setattr(obj, p, row[variable])
                break
        return
    if "Part::" in obj.TypeId:
        for expr in obj.ExpressionEngine:
            if prop == expr[0]:
                obj.setExpression(prop, None)
                obj.recompute()
                break
        for p in obj.PropertiesList:
            if p == prop:
                if obj.getTypeIdOfProperty(p) == 'App::PropertyInteger':
                    setattr(obj, p, int(row[variable]))
                    break
                else:
                    setattr(obj, p, row[variable])
                    break
        return
    if "Spreadsheet" in obj.Module:
        for expr in obj.ExpressionEngine:
            if prop == expr[0]:
                obj.setExpression(prop, None)
                obj.recompute()
                break
        obj.set(prop, row[variable])
        return
