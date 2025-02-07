# -*- coding: utf8 -*-
#****************************************************************************
#*                                                                          *
#*   Printed Circuit Board Workbench for FreeCAD             PCB            *
#*                                                                          *
#*   Copyright (c) 2013-2019                                                *
#*   marmni <marmni@onet.eu>                                                *
#*                                                                          *
#*                                                                          *
#*   This program is free software; you can redistribute it and/or modify   *
#*   it under the terms of the GNU Lesser General Public License (LGPL)     *
#*   as published by the Free Software Foundation; either version 2 of      *
#*   the License, or (at your option) any later version.                    *
#*   for detail see the LICENCE text file.                                  *
#*                                                                          *
#*   This program is distributed in the hope that it will be useful,        *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
#*   GNU Library General Public License for more details.                   *
#*                                                                          *
#*   You should have received a copy of the GNU Library General Public      *
#*   License along with this program; if not, write to the Free Software    *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307   *
#*   USA                                                                    *
#*                                                                          *
#****************************************************************************

import FreeCAD
import os
try:
    import builtins
except:
    import __builtin__ as builtins
import re
from xml.dom import minidom
from PySide import QtCore, QtGui
import FreeCADGui
import time
#
from PCBconf import *
from formats.PCBmainForms import mainPCB
import PCBcheckFreeCADVersion


def insert(filename, other):
    ''' '''
    if os.path.exists(filename):
        open(filename)
    else:
        FreeCAD.Console.PrintError("File does not exist.\n")


def open(filename):
    ''' '''
    result = PCBcheckFreeCADVersion.checkCompatibility()
    if result[0]:
        PCBcheckFreeCADVersion.setDefaultValues()
        #
        kursor = QtGui.QCursor()
        kursor.setShape(QtCore.Qt.ArrowCursor)
        QtGui.QApplication.setOverrideCursor(kursor)
        #
        wersjaFormatu = wersjaFormatuF(filename)
        if wersjaFormatu[0]:
            FreeCAD.Console.PrintMessage("The file was created in {0}.\n".format(wersjaFormatu[1]))
            importBRD(filename, wersjaFormatu[0])
        else:
            FreeCAD.Console.PrintError("Incompatible file format.\n")
        #
        QtGui.QApplication.restoreOverrideCursor()


def wersjaFormatuF(filename):
    ''' '''
    rozsz = os.path.splitext(os.path.basename(filename))[1]
    #
    if rozsz.lower() == ".brd":
        try:  # eagle
            projektBRD = minidom.parse(filename)
            programEagle = projektBRD.getElementsByTagName("eagle")[0].getAttribute("version")
            return ["eagle", "Eagle {0}".format(programEagle)]
        except:
            return [False]
    elif rozsz.lower() == ".lpp":
        try:
            projektBRD = builtins.open(filename, "r").readlines()
            #
            if "LIBREPCB-PROJECT" in projektBRD[0]:
                return ["librepcb", "LibrePCB"]
            else:
                FreeCAD.Console.PrintWarning(u"Not supported file format: {0}.\n".format(version))
                return [False]
        except:
            return [False]
    elif rozsz.lower() == ".hyp":
        try:
            projektBRD = builtins.open(filename, "r").read()
            version = re.findall(r'\{VERSION=(.+?)\}', projektBRD)[0]
            #
            if float(version) >= 2.10:
                return ["hyp_v2", "HyperLynx (version {0})".format(version)]
            else:
                return [False]
        except:
            return [False]
    elif rozsz.lower() in [".idf", ".brd", ".brd", ".emn", ".bdf", ".idb"]:
        try:  # idf v2
            projektBRD = builtins.open(filename, "r").read().replace("\r\n", "\n").replace("\r", "\n")
            ver = re.findall(r'board_file\s+(.+?)\s+', projektBRD)[0]
            return ["idf_v2", "IDF v2"]
        except:
            try:  # idf v3
                ver = re.findall(r'BOARD_FILE\s+(.+?)\s+', projektBRD)[0]
                return ["idf_v3", "IDF v3"]
            except:
                try:  # idf v4
                    FreeCAD.Console.PrintWarning(u"_________________Temporarily disabled_________________\n")
                    return [False]
                    #
                    ver = re.findall(r'IDF_Header \(\nVersion \("4.0"\)', projektBRD)[0]
                    if len(re.findall(r'"Board_Part"', re.findall(r'Board_Part \((.*?)\),', projektBRD, re.DOTALL)[0], re.DOTALL)) == 0:
                        FreeCAD.Console.PrintWarning("No PCB board detected in file.\n")
                        return [False]
                    return ["idf_v4", "IDF v4"]
                except:
                    return [False]
    elif rozsz.lower() == ".kicad_pcb":
        try:  # kicad
            projektBRD = builtins.open(filename, "r").read()
            version = re.findall('^\(kicad_pcb \(version (.+?)\)', projektBRD)[0]
            #
            if version == '3':
                #return ["kicad_v3", "KiCad (version 3)"]
                FreeCAD.Console.PrintWarning(u"KiCad (version 3) is no longer supported.\n".format(version))
                return [False]
            elif version == '4':
                return ["kicad_v4", "KiCad (version 4)"]
            elif int(version[:4]) >= 2016:
                return ["kicad_v4", "KiCad (version {0})".format(version)]
            else:
                FreeCAD.Console.PrintWarning(u"Not supported file format: {0}.\n".format(version))
                return [False]
        except:
            return [False]
    elif rozsz.lower() == ".fcd":
        FreeCAD.Console.PrintWarning(u"_________________Temporarily disabled_________________\n")
        return [False]
        #
        try:  # fidocadj
            projektBRD = builtins.open(filename, "r").read()
            version = re.search('^\[FIDOCAD\]', projektBRD).group()
            return ["fidocadj", "FidoCadJ"]
        except:
            return [False]
    elif rozsz.lower() == ".rzp":
        FreeCAD.Console.PrintWarning(u"_________________Temporarily disabled_________________\n")
        return [False]
        #
        try:  # razen
            import json
            projektBRD = builtins.open(filename, "r")
            projektBRD = json.load(projektBRD)
            # docname = os.path.dirname(filename)
            wersja = projektBRD["version"]
            # projektPCB = projektBRD["layout"]
            # projektBRD = builtins.open(os.path.join(docname, projektPCB), "r")

            return ["razen", "Razen {0}".format(wersja)]
        except:
            return [False]
    elif rozsz.lower() == ".fpc":  # freepcb
        try:
            projektBRD = builtins.open(filename, "r").read()
            wersjaProgramu = re.search('version: (.*)\r\n', projektBRD).groups()[0]
            return ["freepcb", "FreePCB {0}".format(wersjaProgramu)]
            # FreeCAD.Console.PrintError("FreePCB importer is disabled in v3.2!\n")
            # return [False]
        except:
            try:
                projektBRD = builtins.open(filename, "r").read()
                wersjaProgramu = re.search('autosave_interval:', projektBRD).groups()
                return ["freepcb", "FreePCB"]
                # FreeCAD.Console.PrintError("FreePCB importer is disabled in v3.2!\n")
                # return [False]
            except:
                return [False]
    elif rozsz.lower() == ".pcb":  # geda
        projektBRD = builtins.open(filename, "r").read()
        try:
            wersjaProgramu = re.search(r"# release: pcb (.*)", projektBRD).groups()[0]
        except AttributeError:
            try:
                wersjaProgramu = re.search(r"# release: pcb-gtk (.*)", projektBRD).groups()[0]
            except:
                try:
                    wersjaProgramu = re.search(r"# release: pcb.exe (.*)", projektBRD).groups()[0]
                except:
                    return [False]
        ##########################
        # min. required file version 
        fileVersion = 0
        try:
            fileVersion = re.findall(r'FileVersion\[(.+?)\]', projektBRD)[0]
        except:
            pass
        #
        if int(fileVersion) < 20091103:
            FreeCAD.Console.PrintError("File version is too old - min. required version is 20170218. Save file in newer gEDA version. ")
            return [False]
        ##########################
        return ["geda", "gEDA {0}".format(wersjaProgramu)]
    else:
        return [False]


def importBRD(filename, wersjaFormatu):
    ''' '''
    # try:
        # mw = QtGui.qApp.activeWindow()
        # mw.findChild(QtGui.QDockWidget, "Report view").layout().itemAt(0).widget().clear()
    # except AttributeError:  # Linux
        # pass
    mw = FreeCADGui.getMainWindow()
    mw.findChild(QtGui.QDockWidget, "Report view").layout().itemAt(0).widget().clear()
    #
    plytkaPCB = mainPCB(wersjaFormatu, filename)
    plytkaPCB.setProject(filename)
    dial = plytkaPCB.wersjaFormatu.dialogMAIN
    #
    if dial.exec_():
        docname = os.path.splitext(os.path.basename(filename))[0]
        doc = FreeCAD.newDocument(docname)
        ######
        start = time.time()
        #
        plytkaPCB.setProject(filename)
        # adding New Part FC
        newPartObjectFC = plytkaPCB.createDefaultProject(docname)
        #
        plytka = plytkaPCB.generate(doc, newPartObjectFC)
        #
        FreeCAD.Console.PrintWarning('\nTotal time: %i[s]\n' % (time.time() - start))
        ######
        FreeCADGui.ActiveDocument.ActiveView.viewAxometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
        return plytka
