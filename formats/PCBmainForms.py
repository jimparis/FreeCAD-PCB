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
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui
from math import sqrt
import DraftGeomUtils
import Draft
import Part
import os
try:
    import builtins
except:
    import __builtin__ as builtins
import unicodedata
import time
#
import PCBconf
from PCBpartManaging import partsManaging
from PCBfunctions import mathFunctions, getFromSettings_Color_1
from PCBboard import PCBboardObject, viewProviderPCBboardObject
from command.PCBgroups import *
from command.PCBannotations import createAnnotation
from command.PCBglue import createGlue
from command.PCBconstraintAreas import createConstraintArea
from PCBobjects import *

from formats.eagle import EaglePCB
from formats.freepcb import FreePCB
from formats.geda import gEDA_PCB
# from formats.fidocadj import FidoCadJ_PCB
# from formats.razen import Razen_PCB
from formats.kicad_v3 import KiCadv3_PCB
from formats.kicad_v4 import KiCadv4_PCB
from formats.idf_v2 import IDFv2_PCB
from formats.idf_v3 import IDFv3_PCB
from formats.librepcb import LibrePCB
# from formats.idf_v4 import IDFv4_PCB
from formats.hyp import HYP_PCB


class mainPCB(partsManaging):
    def __init__(self, wersjaFormatu, filename, parent=None):
        #reload(PCBconf)
        if wersjaFormatu in ['idf_v2', 'idf_v3']:
            databaseType = 'idf'
        else:
            databaseType = wersjaFormatu
        #
        partsManaging.__init__(self, databaseType)
        self.projektBRD = None
        self.projektBRDName = None
        self.wersjaFormatu = None
        self.tentedVias = [False, False]  # [TOP, BOTTOM]
        #self.padsHeight = [0, 0]  # [TOP, BOTTOM]
        
        if wersjaFormatu == "eagle":
            self.wersjaFormatu = EaglePCB(filename, self)
        elif wersjaFormatu == "freepcb":
            self.wersjaFormatu = FreePCB(filename, self)
        elif wersjaFormatu == "geda":
            self.wersjaFormatu = gEDA_PCB(filename, self)
        #elif wersjaFormatu == "fidocadj":
        #    self.wersjaFormatu = FidoCadJ_PCB(filename, self)
        # elif wersjaFormatu == "razen":
            # self.wersjaFormatu = Razen_PCB()
        elif wersjaFormatu == "kicad_v3":
            self.wersjaFormatu = KiCadv3_PCB(filename, self)
        elif wersjaFormatu == "kicad_v4":
            self.wersjaFormatu = KiCadv4_PCB(filename, self)
        elif wersjaFormatu == "idf_v2":
            self.wersjaFormatu = IDFv2_PCB(filename, self)
        elif wersjaFormatu == "idf_v3":
            self.wersjaFormatu = IDFv3_PCB(filename, self)
        #elif wersjaFormatu == "idf_v4":
        #    self.wersjaFormatu = IDFv4_PCB(filename, self)
        elif wersjaFormatu == "hyp_v2":
            self.wersjaFormatu = HYP_PCB(filename, self)
        elif wersjaFormatu == "librepcb":
            self.wersjaFormatu = LibrePCB(filename, self)

        self.setDatabase()
        
    def setProject(self, filename):
        self.projektBRDName = filename
        self.wersjaFormatu.setProject()
        
    def printInfo(self, data, dataFormat='msg'):
        if self.wersjaFormatu.dialogMAIN.debugImport.isChecked():
            time.sleep(0.05)
            
            if dataFormat == 'error':
                FreeCAD.Console.PrintError(str(data))
            else:
                FreeCAD.Console.PrintMessage(str(data))
            
            #QtGui.qApp.processEvents()
            QtGui.QApplication.processEvents()
    
    def generate(self, doc, newPartObjectFC):
        self.printInfo('\nInitializing')
        # BOARD
        self.generatePCB(doc, newPartObjectFC)
        # HOLES
        self.generateHoles(doc)
        # PARTS
        if self.wersjaFormatu.dialogMAIN.partsBox.isChecked():
            self.importParts()
        # LAYERS
        grp = createGroup_Layers()
        grp_2 = createGroup_Areas()
        #
        pathsLayers = []
        for i in range(self.wersjaFormatu.dialogMAIN.spisWarstw.rowCount()):
            if self.wersjaFormatu.dialogMAIN.spisWarstw.cellWidget(i, 0).isChecked():
                ################
                if self.databaseType in ["geda", "idf", "librepcb", "librepcb"]:
                    layerNumber = self.wersjaFormatu.dialogMAIN.spisWarstw.item(i, 1).text()
                else:
                    layerNumber = int(self.wersjaFormatu.dialogMAIN.spisWarstw.item(i, 1).text())
                #
                layerName = str(self.wersjaFormatu.dialogMAIN.spisWarstw.item(i, 5).text())
                
                try:
                    layerSide = self.wersjaFormatu.dialogMAIN.spisWarstw.cellWidget(i, 3).itemData(self.wersjaFormatu.dialogMAIN.spisWarstw.cellWidget(i, 3).currentIndex())
                except:  
                    layerSide = None
                
                try:
                    layerColor = self.wersjaFormatu.dialogMAIN.spisWarstw.cellWidget(i, 2).getColor()
                except:
                    layerColor = None
                try:
                    layerTransp = self.wersjaFormatu.dialogMAIN.spisWarstw.cellWidget(i, 4).value()
                except:
                    layerTransp = None
                #
                layerFunction = self.wersjaFormatu.defineFunction(layerNumber)
                # ################
                # if self.databaseType == "geda":
                    # layerNumber = int(layerNumber.split("_")[1])
                # ################
                self.printInfo("\nImporting layer '{0}': ".format(layerName))
                try:
                    if layerFunction in ["silk", "pads", "paths"]:
                        if layerFunction == "paths":
                            pathsLayers.append([doc, layerNumber, grp, layerName, layerColor, layerTransp, layerSide, layerFunction, self.wersjaFormatu.dialogMAIN.plytkaPCB_cutHolesThroughAllLayers.isChecked(), self.wersjaFormatu.dialogMAIN.skipEmptyLayers.isChecked()])
                            ########################
                            # tented Vias
                            ########################
                            try:
                                if layerSide == 1:
                                    if not self.tentedVias[0]:
                                        self.tentedVias[0] = layerColor
                                    else:
                                        self.tentedVias[0].ViewObject.ShapeColor = layerColor
                                elif layerSide == 0:
                                    if not self.tentedVias[1]:
                                        self.tentedVias[1] = layerColor
                                    else:
                                        self.tentedVias[1].ViewObject.ShapeColor = layerColor
                            except:
                                pass
                        #
                        self.generateSilkLayer(doc, layerNumber, grp, layerName, layerColor, layerTransp, layerSide, layerFunction, self.wersjaFormatu.dialogMAIN.plytkaPCB_cutHolesThroughAllLayers.isChecked(), self.wersjaFormatu.dialogMAIN.skipEmptyLayers.isChecked(), self.wersjaFormatu.dialogMAIN.tentedViasLimit.value(), False)
                        ########################
                        # tented Vias
                        ########################
                        if layerFunction == "pads" and self.wersjaFormatu.dialogMAIN.tentedViasLimit.value() > 0:
                            color = getFromSettings_Color_1('PathColor', 7012607)
                            layerColor = (color[0] / 255., color[1] / 255., color[2] / 255.)
                            
                            try:
                                if layerSide == 1:
                                    if self.tentedVias[0]:
                                        layerColor = self.tentedVias[0]
                                elif layerSide == 0:
                                    if self.tentedVias[1]:
                                       layerColor = self.tentedVias[1]
                            except:
                                pass
                            #
                            obj = self.generateSilkLayer(doc, layerNumber, grp, layerName + "_tentedVias", layerColor, layerTransp, layerSide, layerFunction, self.wersjaFormatu.dialogMAIN.plytkaPCB_cutHolesThroughAllLayers.isChecked(), self.wersjaFormatu.dialogMAIN.skipEmptyLayers.isChecked(), self.wersjaFormatu.dialogMAIN.tentedViasLimit.value(), True)
                            #
                            try:
                                if layerSide == 1:
                                    if not self.tentedVias[0]:
                                        self.tentedVias[0] = obj
                                elif layerSide == 0:
                                    if not self.tentedVias[1]:
                                       self.tentedVias[1] = obj
                            except:
                                pass
                    #
                    elif layerFunction == "measures":
                        self.generateDimensions(doc, grp, layerName, layerColor, self.wersjaFormatu.dialogMAIN.gruboscPlytki.value())
                    elif layerFunction == "glue":
                        self.generateGlue(doc, grp, layerName, layerColor, layerNumber, layerSide)
                    elif layerFunction == "constraint":
                        self.generateConstraintAreas(doc, layerNumber, grp, layerName, layerColor, layerTransp)
                    elif layerFunction == "annotations":
                        self.addAnnotations(self.wersjaFormatu.getNormalAnnotations(), layerColor)
                except Exception as e:
                    self.printInfo('{0}'.format(e), 'error')
                else:
                    self.printInfo('\n\tdone')
        #
        if self.wersjaFormatu.dialogMAIN.copperImportPolygons.isChecked():
            self.generatePolygonsOnCopperLayer(pathsLayers)
    
    def importParts(self):
        koloroweElemnty = self.wersjaFormatu.dialogMAIN.plytkaPCB_elementyKolory.isChecked()
        adjustParts = self.wersjaFormatu.dialogMAIN.adjustParts.isChecked()
        groupParts = self.wersjaFormatu.dialogMAIN.plytkaPCB_grupujElementy.isChecked()
        partMinX = self.wersjaFormatu.dialogMAIN.partMinX.value()
        partMinY = self.wersjaFormatu.dialogMAIN.partMinY.value()
        partMinZ = self.wersjaFormatu.dialogMAIN.partMinZ.value()
        #
        self.printInfo('\nImporting parts: ')
        errors = []
        
        for i in self.wersjaFormatu.getParts():
            self.printInfo('\n    {0} ({1}): '.format(i["name"], i["package"]))
            result = self.addPart(i, koloroweElemnty, adjustParts, groupParts, partMinX, partMinY, partMinZ)
        
            if self.wersjaFormatu.dialogMAIN.plytkaPCB_plikER.isChecked() and result[0] == 'Error':
                partNameTXT = self.generateNewLabel(i["name"])
                if isinstance(partNameTXT, str):
                    partNameTXT = unicodedata.normalize('NFKD', partNameTXT).encode('ascii', 'ignore')
                
                #errors.append([partNameTXT, i['package'], i['value'], i['library']])
                errors.append([partNameTXT, i["package"], i["value"], i["library"]])
                self.printInfo('error', 'error')
            else:
                self.printInfo('done')
        
        if self.wersjaFormatu.dialogMAIN.plytkaPCB_plikER.isChecked() and len(errors):
            self.generateErrorReport(errors, self.projektBRDName)
    
    def generateGlue(self, doc, grp, layerName, layerColor, layerNumber, layerSide):
        for i, j in self.wersjaFormatu.getGlue([layerNumber, layerName]).items():
            ser = doc.addObject('Sketcher::SketchObject', "Sketch_{0}".format(layerName))
            ser.ViewObject.Visibility = False
            for k in j:
                if k[0] == 'line':
                    ser.addGeometry(Part.LineSegment(FreeCAD.Vector(k[1], k[2], 0), FreeCAD.Vector(k[3], k[4], 0)))
                elif k[0] == 'circle':
                    ser.addGeometry(Part.Circle(FreeCAD.Vector(k[1], k[2]), FreeCAD.Vector(0, 0, 1), k[3]))
                elif k[0] == 'arc':
                    x1 = k[1]
                    y1 = k[2]
                    x2 = k[3]
                    y2 = k[4]
                    [x3, y3] = self.arcMidPoint([x2, y2], [x1, y1], k[5])
                    
                    arc = Part.ArcOfCircle(FreeCAD.Vector(x1, y1, 0.0), FreeCAD.Vector(x3, y3, 0.0), FreeCAD.Vector(x2, y2, 0.0))
                    ser.addGeometry(arc)
            #
            glue = createGlue()
            glue.base = ser
            glue.width = i
            glue.side = layerSide
            glue.color = layerColor
            glue.generate()
            #glue.recompute()

    def generatePolygonsOnCopperLayer(self, pathsLayers):
        for i in pathsLayers: # i = doc, layerNumber, grp, layerNameO, layerColor, defHeight, layerSide, layerVariant, cutHoles, skipEmptyLayers
            [doc, layerNumber, grp, layerNameO, layerColor, defHeight, layerSide, layerVariant, cutHoles, skipEmptyLayers] = i
            #
            layerName = "{0}_{1}".format(layerNameO, layerNumber)
            layerType = [layerName, "paths", "polygon"]
            #
            layerS = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", layerName)
            layerNew = layerSilkObject(layerS, layerType)
            layerNew.holes = self.showHoles()
            layerNew.side = layerSide
            layerNew.defHeight = defHeight
            layerNew.Cut = cutHoles
            #
            self.wersjaFormatu.getPolygonsFromCopperLayer(layerNew, [layerNumber, layerNameO], [False, False, False, True])
            #
            pcb = getPCBheight()
            data = []
            # nS= None
            
            for j in pcb[2].Group:
                if hasattr(j, "Proxy") and hasattr(j.Proxy, "Type") and isinstance(j.Proxy.Type, list) and ("paths" in j.Proxy.Type or "pads" in j.Proxy.Type) and not "polygon" in j.Proxy.Type:
                    pozZ = j.Placement.Base.z
                    j.Placement.Base.z = 0
                    try:
                        for k in range(0, len(j.Shape.Compounds[0].Solids)):
                            solid = j.Shape.Compounds[0].Solids[k]
                            #
                            if k in j.Proxy.signalsList.keys() and j.Proxy.signalsList[k] == layerNew.signalsList[0][0]:
                                continue
                            else:
                                if solid.isValid() and layerNew.spisObiektowTXT[0].distToShape(solid)[0] == 0.0:
                                    try:
                                        a = solid.makeOffsetShape(layerNew.signalsList[0][1], 0.01, join=0)
                                        if not a.isNull():
                                            #######################################################################
                                            #too slow solution -> testing board 227[s]
                                            # common = layerNew.spisObiektowTXT[0].common(a)
                                            # layerNew.spisObiektowTXT[0] = layerNew.spisObiektowTXT[0].cut(common)
                                            ######################################################################
                                            #too slow solution -> testing board 183[s]
                                            # layerNew.spisObiektowTXT[0] = layerNew.spisObiektowTXT[0].cut(a)
                                            ######################################################################
                                            # only cutting -> testing board 9[s]
                                            new = layerNew.spisObiektowTXT[0]
                                            data.append(new.cut(a))
                                            ######################################################################
                                            #too slow solution -> testing board 160[s]
                                            # if not nS:
                                                # nS = a
                                            # else:
                                                # nS = nS.fuse(a)
                                            ######################################################################
                                    except Exception as e:
                                        print(e)
                    except Exception as e:
                        print(e)
                    j.Placement.Base.z = pozZ
            #
            # layerNew.spisObiektowTXT[0] = layerNew.spisObiektowTXT[0].cut(nS)
            if len(data):
                pass
                #######################################################################
                #too slow solution -> testing board 237[s]
                # out =[]
                # for i in range(0, len(data)):
                    # Part.show(data[i])
                # for i in FreeCAD.ActiveDocument.Objects:
                    # if i.Label.startswith("Shape"):
                        # out.append(i)
                # a = FreeCAD.ActiveDocument.addObject("Part::MultiCommon","Common")
                # a.Shapes = out
                # FreeCAD.ActiveDocument.recompute()
                #######################################################################
                #testing board 139[s]
                for i in range(0, len(data)):
                    a = layerNew.spisObiektowTXT[0]
                    layerNew.spisObiektowTXT[0] = layerNew.spisObiektowTXT[0].common([data[i]])
                    #Part.show(data[i])
                    if not len(layerNew.spisObiektowTXT[0].Solids):
                       layerNew.spisObiektowTXT[0] = a
            #
            if skipEmptyLayers and not(layerS.Proxy.spisObiektowTXT):
                self.printInfo("\n\tLayer is empty", 'error')
                FreeCAD.ActiveDocument.removeObject(layerS.Label)
                return
            #
            layerNew.generuj(layerS)
            layerNew.updatePosition_Z(layerS, pcb[1])
            viewProviderLayerSilkObject(layerS.ViewObject)
            layerS.ViewObject.ShapeColor = layerColor
            #
            grp.addObject(layerS)
            #
            pcb[2].Proxy.addObject(pcb[2], layerS)
    
    def generateSilkLayer(self, doc, layerNumber, grp, layerNameO, layerColor, defHeight, layerSide, layerVariant, cutHoles, skipEmptyLayers, tentedViasLimit, tentedVias):
        try:
            layerName = "{0}_{1}".format(layerNameO, layerNumber)
            #layerSide = softLayers[self.wersjaFormatu.databaseType][layerNumber]['side']
            layerType = [layerName]
            if layerVariant == "paths":
                layerType.append("paths")
            elif layerVariant == "pads":
                layerType.append("pads")
            elif layerVariant == "silk":
                layerType.append("silk")
            #
            layerS = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", layerName)
            layerNew = layerSilkObject(layerS, layerType)
            
            #layerNew.holes = self.showHoles()
            layerNew.side = layerSide
            layerNew.defHeight = defHeight
            layerS.Cut = cutHoles
            #
            if layerVariant == "paths":
                self.wersjaFormatu.getSilkLayer(layerNew, [layerNumber, layerNameO], [True, True, True, False])
                self.wersjaFormatu.getPaths(layerNew, [layerNumber, layerNameO], [True, True, True, False])
                self.wersjaFormatu.getSilkLayerModels(layerNew, [layerNumber, layerNameO])
            else:
                if layerVariant == "silk" or layerVariant == "pads" and self.databaseType != "geda":
                    self.wersjaFormatu.getSilkLayer(layerNew, [layerNumber, layerNameO])
                    self.wersjaFormatu.getSilkLayerModels(layerNew, [layerNumber, layerNameO])
                if layerVariant == "pads":
                    self.wersjaFormatu.getPads(layerNew, [layerNumber, layerNameO], layerSide, tentedViasLimit, tentedVias)
            #
            pcb = getPCBheight()
            #
            if skipEmptyLayers and not(layerS.Proxy.spisObiektowTXT):
                self.printInfo("\n\tLayer is empty", 'error')
                FreeCAD.ActiveDocument.removeObject(layerS.Label)
                return
            #
            layerNew.generuj(layerS)
            layerNew.updatePosition_Z(layerS, pcb[1])
            viewProviderLayerSilkObject(layerS.ViewObject)
            layerS.ViewObject.ShapeColor = layerColor
            #
            grp.addObject(layerS)
            #
            pcb[2].Proxy.addObject(pcb[2], layerS)
            return layerS
            #FreeCADGui.activeDocument().getObject(layerS.Name).DisplayMode = 1
        except Exception as e:
            print(e)
    
    def generateDimensions(self, doc, layerGRP, layerName, layerColor, gruboscPlytki):
        layerName = "{0}".format(layerName)
        grp = createGroup_Dimensions(layerName)
        
        for i in self.wersjaFormatu.getDimensions():
            x1 = i[0]
            y1 = i[1]
            x2 = i[2]
            y2 = i[3]
            x3 = i[4]
            y3 = i[5]
            dtype = i[6]
            
            if dtype in ["angle"]:
                continue
            
            #dim = Draft.makeDimension(FreeCAD.Vector(x1, y1, gruboscPlytki), FreeCAD.Vector(x2, y2, gruboscPlytki), FreeCAD.Vector(x3, y3, gruboscPlytki))
            dim = Draft.make_linear_dimension(FreeCAD.Vector(x1, y1, gruboscPlytki), FreeCAD.Vector(x2, y2, gruboscPlytki), FreeCAD.Vector(x3, y3, gruboscPlytki))
            dim.ViewObject.LineColor = layerColor
            dim.ViewObject.LineWidth = 1.00
            dim.ViewObject.ExtLines = 0.00
            dim.ViewObject.FontSize = 2.00
            dim.ViewObject.ArrowSize = '0.5 mm'
            dim.ViewObject.ArrowType = "Arrow"
            grp.addObject(dim)
        
        layerGRP.addObject(grp)
    
    def generatePCB(self, doc, newPartObjectFC):
        gruboscPlytki = self.wersjaFormatu.dialogMAIN.gruboscPlytki.value()
        #
        self.printInfo('\nGenerate board: ')
        try:
            groupBRD = createGroup_PCB()
            #
            doc.addObject('Sketcher::SketchObject', 'PCB_Border')
            doc.PCB_Border.Placement = FreeCAD.Placement(FreeCAD.Vector(0.0, 0.0, 0.0), FreeCAD.Rotation(0.0, 0.0, 0.0, 1.0))
            #
            self.wersjaFormatu.getPCB(doc.PCB_Border)
            #
            PCBboard = doc.addObject("Part::FeaturePython", "Board")
            PCBboardObject(PCBboard)
            PCBboard.Thickness = gruboscPlytki
            PCBboard.Border = doc.PCB_Border
            PCBboard.Parent = newPartObjectFC
            viewProviderPCBboardObject(PCBboard.ViewObject)
            groupBRD.addObject(doc.Board)
            FreeCADGui.activeDocument().getObject(PCBboard.Name).ShapeColor = PCBconf.PCB_COLOR
            FreeCADGui.activeDocument().PCB_Border.Visibility = False
            PCBboard.purgeTouched()
            self.updateView()
        except Exception as e:
            self.printInfo(u'{0}'.format(e), 'error')
        else:
            self.printInfo('done')
        
    def generateHoles(self, doc):
        self.printInfo('\nGenerate holes: ')
        try:
            doc.addObject('Sketcher::SketchObject', 'PCB_Holes')
            doc.PCB_Holes.Placement = FreeCAD.Placement(FreeCAD.Vector(0.0, 0.0, 0.0), FreeCAD.Rotation(0.0, 0.0, 0.0, 1.0))
            FreeCADGui.activeDocument().PCB_Holes.Visibility = False
            #
            Hmin = self.wersjaFormatu.dialogMAIN.holesMin.value()
            Hmax = self.wersjaFormatu.dialogMAIN.holesMax.value()
            types = {'H':self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyH.isChecked(), 'V':self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyV.isChecked(), 'P':self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyP.isChecked(), "IH":self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyIH.isChecked()}
            
            self.wersjaFormatu.getHoles(doc.PCB_Holes, types, Hmin, Hmax)
            #
            doc.Board.Holes = doc.PCB_Holes
            doc.recompute()
        except Exception as e:
            self.printInfo(u'\t{0}'.format(e), 'error')
        else:
            self.printInfo('done')
    
    def Draft2Sketch(self, elem, sketch):
        return (DraftGeomUtils.geom(elem.toShape().Edges[0], sketch.Placement))
    
    def generateConstraintAreas(self, doc, layerNumber, grp, layerName, layerColor, layerTransparent):
        typeL = PCBconf.softLayers[self.databaseType][layerNumber]['ltype']
        
        for i in self.wersjaFormatu.getConstraintAreas(layerNumber):
            ser = doc.addObject('Sketcher::SketchObject', "Sketch_{0}".format(layerName))
            ser.ViewObject.Visibility = False
            #
            if i[0] == 'rect':
                try:
                    height = i[5]
                except:
                    height = 0
                
                x1 = i[1]
                y1 = i[2]
                
                x2 = i[3]
                y2 = i[2]
                
                x3 = i[3]
                y3 = i[4]
                
                x4 = i[1]
                y4 = i[4]
                
                try:
                    if i[6] != 0:
                        xs = (i[1] + i[3]) / 2.
                        ys = (i[2] + i[4]) / 2.
                
                        mat = mathFunctions()
                        (x1, y1) = mat.obrocPunkt2([x1, y1], [xs, ys], i[6])
                        (x2, y2) = mat.obrocPunkt2([x2, y2], [xs, ys], i[6])
                        (x3, y3) = mat.obrocPunkt2([x3, y3], [xs, ys], i[6])
                        (x4, y4) = mat.obrocPunkt2([x4, y4], [xs, ys], i[6])
                except:
                    pass
                
                ser.addGeometry(Part.LineSegment(FreeCAD.Vector(x1, y1, 0), FreeCAD.Vector(x2, y2, 0)))
                ser.addGeometry(Part.LineSegment(FreeCAD.Vector(x2, y2, 0), FreeCAD.Vector(x3, y3, 0)))
                ser.addGeometry(Part.LineSegment(FreeCAD.Vector(x3, y3, 0), FreeCAD.Vector(x4, y4, 0)))
                ser.addGeometry(Part.LineSegment(FreeCAD.Vector(x4, y4, 0), FreeCAD.Vector(x1, y1, 0)))
            elif i[0] == 'circle':
                try:
                    try:
                        height = i[5]
                    except:
                        height = 0
                    
                    if i[4] == 0:
                        ser.addGeometry(Part.Circle(FreeCAD.Vector(i[1], i[2], 0), FreeCAD.Vector(0, 0, 1), i[3]),False)
                    else:
                        ser.addGeometry(Part.Circle(FreeCAD.Vector(i[1], i[2], 0), FreeCAD.Vector(0, 0, 1), i[3] + i[4] / 2))
                        ser.addGeometry(Part.Circle(FreeCAD.Vector(i[1], i[2], 0), FreeCAD.Vector(0, 0, 1), i[3] - i[4] / 2))
                except Exception as e:
                    FreeCAD.Console.PrintWarning("3. {0}\n".format(e))
            elif i[0] == 'polygon':
                try:
                    height = i[2]
                except:
                    height = 0
                
                for j in i[1]:
                    if j[0] == 'Line':
                        ser.addGeometry(Part.LineSegment(FreeCAD.Vector(j[1], j[2], 0), FreeCAD.Vector(j[3], j[4], 0)))
                    elif j[0] == 'Arc3P':
                        x1 = j[1]
                        y1 = j[2]
                        x2 = j[3]
                        y2 = j[4]
                        [x3, y3] = self.arcMidPoint([x2, y2], [x1, y1], j[5])
                        
                        arc = Part.ArcOfCircle(FreeCAD.Vector(x1, y1, 0.0), FreeCAD.Vector(x3, y3, 0.0), FreeCAD.Vector(x2, y2, 0.0))
                        ser.addGeometry(arc)
            #
            #FreeCAD.ActiveDocument.recompute()
            ser.recompute()
            createConstraintArea(ser, typeL, height)
            self.updateView()
            #FreeCAD.ActiveDocument.recompute()
    
    def generateOctagon(self, x, y, height, width=0):
        if width == 0:
            width = height
        
        w_pP = width / 2.
        w_zP = width / (2 + (sqrt(2)))
        w_aP = width * (sqrt(2) - 1)
        
        h_pP = height / 2.
        h_zP = height / (2 + (sqrt(2)))
        h_aP = height * (sqrt(2) - 1)
        
        return [[x - w_pP + w_zP, y - h_pP, 0, x - w_pP + w_zP + w_aP, y - h_pP, 0],
                [x - w_pP + w_zP + w_aP, y - h_pP, 0, x + w_pP, y -h_pP + h_zP, 0],
                [x + w_pP, y - h_pP + h_zP, 0, x + w_pP, y - h_pP + h_zP + h_aP, 0],
                [x + w_pP, y - h_pP + h_zP + h_aP, 0, x + w_pP - w_zP, y + h_pP, 0],
                [x + w_pP - w_zP, y + h_pP, 0, x + w_pP - w_zP - w_aP, y + h_pP, 0],
                [x + w_pP - w_zP - w_aP, y + h_pP, 0, x - w_pP, y + h_pP - h_zP, 0],
                [x - w_pP, y + h_pP - h_zP, 0, x - w_pP, y + h_pP - h_zP - h_aP, 0],
                [x - w_pP, y + h_pP - h_zP - h_aP, 0, x - w_pP + w_zP, y - h_pP, 0]]

    #def generateOctagon(self, x, y, diameter):
        #pP = diameter / 2.
        #zP = diameter / (2 + (sqrt(2)))
        #aP = diameter * (sqrt(2) - 1)
        
        #return [[x - pP + zP, y - pP, 0, x - pP + zP + aP, y - pP, 0],
                #[x - pP + zP + aP, y - pP, 0, x + pP, y - pP + zP, 0],
                #[x + pP, y - pP + zP, 0, x + pP, y - pP + zP + aP, 0],
                #[x + pP, y - pP + zP + aP, 0, x + pP - zP, y + pP, 0],
                #[x + pP - zP, y + pP, 0, x + pP - zP - aP, y + pP, 0],
                #[x + pP - zP - aP, y + pP, 0, x - pP, y + pP - zP, 0],
                #[x - pP, y + pP - zP, 0, x - pP, y + pP - zP - aP, 0],
                #[x - pP, y + pP - zP - aP, 0, x - pP + zP, y - pP, 0]]
    
    def showHoles(self):
        if not self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyH.isChecked() and not self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyV.isChecked() and not self.wersjaFormatu.dialogMAIN.plytkaPCB_otworyP.isChecked():
            return False
        else:
            return True

    def generateErrorReport(self, PCB_ER, filename):
        ############### ZAPIS DO PLIKU - LISTA BRAKUJACYCH ELEMENTOW
        if PCB_ER and len(PCB_ER):
            if os.path.exists(filename) and os.path.isfile(filename):
                (path, docname) = os.path.splitext(os.path.basename(filename))
                plik = builtins.open(u"{0}.err".format(filename), "w")
                a = []
                a = [i for i in PCB_ER if str(i) not in a and not a.append(str(i))]
                PCB_ER = list(a)
                
                FreeCAD.Console.PrintWarning("**************************\n")
                for i in PCB_ER:
                    line = u"Object not found: {0} {2} [Package: {1}, Library: {3}]\n".format(i[0], i[1], i[2], i[3])
                    plik.writelines(line)
                    FreeCAD.Console.PrintWarning(line)
                FreeCAD.Console.PrintWarning("**************************\n")
                plik.close()
            else:
                FreeCAD.Console.PrintWarning("Access Denied. The Specified Path does not exist, or there could be permission problem.")
        else:
            try:
                os.remove("{0}.err".format(filename))
            except:
                pass
        ##############
        
    def addAnnotations(self, annotations, color):
        for i in annotations:
            #FreeCAD.Console.PrintWarning("{0}\n".format(i))
            annotation = createAnnotation()
            annotation.X = i["x"]
            annotation.Y = i["y"]
            annotation.Z = i["z"]
            annotation.Side = i["side"]
            annotation.Rot = i["rot"]
            annotation.Text = i["text"]
            annotation.Align = i["align"]
            annotation.Size = i["size"]
            annotation.Spin = i["spin"]
            annotation.tracking = i["tracking"]
            annotation.lineDistance = i["distance"]
            annotation.Color = color
            annotation.Font = i["font"]
            annotation.Visibility = i["display"]
            annotation.mode = i["mode"]
            annotation.generate()
