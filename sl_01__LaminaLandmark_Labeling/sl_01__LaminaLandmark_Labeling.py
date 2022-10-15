#########################################################################
# Copyright (C)                                                       	#
# 2022-October Sen Li (Sen.Li.1@ens.etsmtl.ca)							#
# Permission given to modify the code only for Non-Profit Research		#
# as long as you keep this declaration at the top 						#
#########################################################################
import logging
import os

import vtk, qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog


import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import numpy as np
import time

'''=================================================================================================================='''
'''=================================================================================================================='''
'''------------------------- STRING Macro of  sl_01__LaminaLandmark_Labeling ----------------------------------------'''
'''------------------------------------------------------------------------------------------------------------------'''
INT_SliderFrameIndex_Min                = 1       # StartingValue of slider_FrameIndex, increase from 1
INT_FRAME_INDEX_SLIDER_DEFAULT          = 50      # Default slider_FrameIndex value
INT_FRAME_INDEX_SLIDER_DEFAULT_MAX      = 99      # Default slider_FrameIndex maximum

# ReferenceRole
STR_SeqBrowserNode_RefRole_Selected     = 'SeqBrowser_Ref_CurSelected'
STR_pListNode_RefRole_LandmarkProxy     = 'pListNodeRef_Proxy'   # PointListNode_RefRole_Proxy_curFrame_LaminaeLandmarks

STR_CurveNode_RefRole_LeftLamina    = 'curveNodeRef_LeftLamina'  # Locate CurveNode from SeqBrowser / SequenceLandmark
STR_CurveNode_RefRole_RightLamina   = 'curveNodeRef_RightLamina' # Locate CurveNode from SeqBrowser / SequenceLandmark
STR_CurveNode_RefRole_SpinalCord    = 'curveNodeRef_SpinalCord'  # Locate CurveNode from SeqBrowser / SequenceLandmark
STR_SeqBrowserNode_RefRole_Parent   = 'seqBrowserNodeRef_Parent' # Locate Parent_SequenceBrowser from CurveNode

# AttributeName of LandmarkProxyNode
STR_AttriName__Idx_ControlPoint_MousePicked = 'idx_ControlPoint_MousePicked' # LandmarkProxyNode locating Drag/Picked ControlPoint
STR_TRUE = 'True'
STR_FALSE = 'False'

# AttributeName of SequenceLandmark_PointListNode
STR_AttriName_NodePointList_isNegativeFrame = 'isNegativeFrame' # Corresponds to uiCheckBox and LandmarkPositionLabel
# AttributeName of Landmark_Curves:     LIST_LandmarkCurveType
STR_AttriName_LandmarkType  = 'LandmarkType'    # can be one of LIST_LandmarkCurveType, For node_LandmarkCurve
STR_AttriName_isCurve3PointsDisplay = 'isCurve3PointsDisplay' # whether to display in 3D widget or not

#   STR  LandmarkPointList ---------------------------------------------------------------------------------------------
STR_NodeName_SeqBrowserProxy_Landmarks  = 'Proxy_pList_Landmarks'  # NodeName_SeqBroswerProxy_Landmarks__PointList
STR_NodeName_SeqBrowserProxy_2DScan     = 'Image_Transducer'
STR_NodeName_SeqBrowserProxy_LinearTransform = 'ProbeToTracker'
STR_NodeName_CrossHair                  = 'Crosshair'

# ------------------------------------------------------------------------------------------------------------------
STR_LabelButton_Sequential      = 'Sequential'      # to test for the persistent status

STR_LandmarkType_LeftLamina     = 'LeftLamina'
STR_LandmarkType_RightLamina    = 'RightLamina'
LIST_LANDMARK_TYPE  = [STR_LandmarkType_LeftLamina, STR_LandmarkType_RightLamina]

STR_LandmarkCurveType_SpinalCord    =  'SpinalCord' # curve_SpinalCord is the center curve of curve_LeftLamina & curve_RightLamina
LIST_LandmarkCurveType              =  LIST_LANDMARK_TYPE + [STR_LandmarkCurveType_SpinalCord]  # Vertebral Landmark CurveTypes in each SeqBrowser
STR_ControlPointLabelShort_SpinalCord =  'SC' # SpinalCord is calculated, does not belong to LIST_LANDMARK_PREFIX

STR_ControlPointLabelPrefix_Left    = 'L'
STR_ControlPointLabelPrefix_Right   = 'R'
LIST_LANDMARK_PREFIX = [STR_ControlPointLabelPrefix_Left, STR_ControlPointLabelPrefix_Right]    # Vertical-Index of NumpyLandmarks

def getDict_LandmarkLabelsToUpdate():
    dict_LandmarksToUpdate = {}
    for str_LandmarkPrefix in LIST_LANDMARK_PREFIX:
        dict_LandmarksToUpdate[str_LandmarkPrefix] = True
    return dict_LandmarksToUpdate

# ------------------------------------------------------------------------------------------------------------------
STR_FRAME_TYPE_CURRENT  = 'curFrame'
STR_FRAME_TYPE_PREVIOUS = 'preFrame'
STR_FRAME_TYPE_NEXT     = 'nextFrame'

STR_QLabel_StyleSheet_Allert = "QLabel { background-color : rgb(255, 110, 110); color : blue; font: bold; }"
STR_QLabel_StyleSheet_onLandmarkMouseDrag = "QLabel { background-color : rgb(100, 255, 100); font: bold; }"

# ------------------------------------------------------------------------------------------------------------------
INT_DEFAULT_RAS_VALUE       = 999999
INT_NEGATIVE_RAS_VALUE      = -999999

STR_NumpyLandmark_Var_I     = 'I_Row'       # row       address from    image bottom
STR_NumpyLandmark_Var_J     = 'J_Col'       # column    address from    image left
STR_NumpyLandmark_Var_R     = 'Right'       # from left         towards right
STR_NumpyLandmark_Var_A     = 'Anterior'    # from posterior    towards anterior
STR_NumpyLandmark_Var_S     = 'Superior'    # from inferior     towards superior
NumVar_NumpyLandmark_RAS   = 3             # Number of variables of one landmark in RAS coordinate system
LIST_NumpyLandmark_VarType = [STR_NumpyLandmark_Var_I, STR_NumpyLandmark_Var_J,   \
                              STR_NumpyLandmark_Var_R, STR_NumpyLandmark_Var_A, STR_NumpyLandmark_Var_S]

# ------------------------------------------------------------------------------------------------------------------
'''=================================================================================================================='''
#
# sl_01__LaminaLandmark_Labeling
#
class sl_01__LaminaLandmark_Labeling(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Lamina Landmark Labeling"
        self.parent.categories = ["SL_SpineUS"]         # Set categories (the module shows up in the module selector)
        self.parent.dependencies = ['Markups', 'Sequences']          # Add here list of module names that this module requires
        self.parent.contributors = ["Sen Li"]   # Replace with "Firstname Lastname (Organization)"
        # TODO:     10. update with a link to online module Tutorial
        self.parent.helpText = """This is sl_01__LaminaLandmark_Labeling ! """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = 'Spine Deformity Analysis using Freehand 3D Ultrasound. \nThis file was originally developed by Sen Li, LATIS, École de techonologie supérieure. \nSen.Li.1@ens.etsmtl.ca'

        print("sl_01__LaminaLandmark_Labeling(Module):    __init__(self, parent)")

'''=================================================================================================================='''
class sl_01__LaminaLandmark_LabelingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

    def __init__(self, parent=None):
        """    Called when the user opens the module the first time and the widget is initialized.    """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None  # SingleTon initialized through self.setParameterNode(self.logic.getParameterNode())
        self._updatingGUIFromParameterNode = False

        self.uiObserverTag_LandmarkProxyNode_PointPositionDefined = None
        self.dict_uiObserverTag_onClickCurveControlPoint = {}
        print("**Widget.__init__(self, parent)")

    def setup(self):
        """    00. Called when the user opens the module the first time and the widget is initialized. """''''''
        ScriptedLoadableModuleWidget.setup(self)

        # 01. Load widget from .ui file (created by Qt Designer).
        #       Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/sl_01__LaminaLandmark_Labeling.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # 02. Set scene in MRML widgets. Make sure that in Qt designer the
        #       top-level qMRMLWidget's   "mrmlSceneChanged(vtkMRMLScene*)" signal in   is connected to
        #       each      MRML widget's   "setMRMLScene(vtkMRMLScene*)"     slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # 03. Create logic class. Logic implements all computations that should be possible to run
        #       in batch mode, without a graphical user interface.
        self.logic = sl_01__LaminaLandmark_LabelingLogic()

        # 04. Connections, ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        print("**Widget.setup(self), \tSL_Developer, A")
        # 05. SL_Developer, A: Connect Signal-Slot,  ensure that whenever user changes some settings on the GUI,
        #                                         that is saved in the MRML scene (in the selected parameter node).
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.on_mrmlScene_EndImport)

        self.ui.sequenceSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectedNodeChanged)
        slicer.modules.sequences.toolBar().activeBrowserNodeChanged.connect(self.onSelectedNodeChanged)

        self.ui.slider_SeqFrame.connect("valueChanged(int)", self.onSliderFrameIndex_ValueChanged)

        self.ui.pushButton_DropLeft.clicked.connect(self.onPushButton_DropLeft_Clicked)
        self.ui.pushButton_StartSeqLabeling.clicked.connect(self.onPushButton_StartSeqLabeling_Clicked)
        self.ui.pushButton_DropRight.clicked.connect(self.onPushButton_DropRight_Clicked)

        self.ui.pushButton_DeleteLeft.clicked.connect(self.onPushButton_DeleteLeft_Clicked)
        self.ui.pushButton_DeleteFrameLandmark.clicked.connect(self.onPushButton_DeleteFrameLandmark_Clicked)
        self.ui.pushButton_DeleteRight.clicked.connect(self.onPushButton_DeleteRight_Clicked)

        self.ui.checkBox_Negative_curFrame.clicked.connect(self.onCheckBox_Negative_curFrame_Clicked)

        self.ui.pushButton_Output_SeqNumpyLandmarks.clicked.connect(self.onPushButton_Output_SeqNumpyLandmarks_Clicked)
        self.ui.pushButton_Load_SeqNumpyLandmarks.clicked.connect(self.onPushButton_Load_SeqNumpyLandmarks_Clicked)

        # SL_Notes: can only be put here; Not able to disconnect, cannot be put into ener() or initializeParameterNode()
        self.initializeShortCut()   # Otherwise, if exit() and re-enter(), shortcut will not be functional; not sure why

        # 06. Needed for programmer-friendly  Module-Reload   where the Module had already been enter(self)-ed;
        #                                     Otherwise,      will initial through function     enter(self)
        if self.parent.isEntered:
            self.initializeParameterNode()  # Every-Module own a SingoleTon ParameterNode track by **Logic.moduleName!

    # ------------------------------------------------------------------------------------------------------------------
    def cleanup(self):
        """    Called when the application closes and the module widget is destroyed.    """''''''
        print("**Widget.cleanup(self)")

        self.removeObservers()

    def enter(self):
        """    Called each time the user opens this module.    """''''''
        print("**Widget.enter(self)")

        # 01. Slicer.  SL__Note:   Every-Module own a SingoleTon ParameterNode that can be identified by
        #                                 self._parameterNode.GetAttribute('ModuleName')!  Need to initial every Entry!
        self.initializeParameterNode()

    # ------------------------------------------------------------------------------------------------------------------
    def exit(self):
        """    Called each time the user opens a different module.    """''''''
        print("**Widget.exit(self)")
        # Slicer. Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # ------------------------------------------------------------------------------------------------------------------
    def onSceneStartClose(self, caller, event):
        """    Called just before the scene is closed.    """''''''
        print("**Widget.onSceneStartClose(self, caller, event)")

        # 01.SL_Developer, F-Slot:  Before Reset ParameterNode, ReSet our own ui_Observer
        if self._parameterNode:
            nMS_SeqBrowserProxy_Landmarks = self._parameterNode.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            if nMS_SeqBrowserProxy_Landmarks and self.uiObserverTag_LandmarkProxyNode_PointPositionDefined:
                nMS_SeqBrowserProxy_Landmarks.RemoveObserver(self.uiObserverTag_LandmarkProxyNode_PointPositionDefined)
        self.uiObserverTag_LandmarkProxyNode_PointPositionDefined   = None
        self.dict_uiObserverTag_onClickCurveControlPoint = {}

        # 02. Slicer.   Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    # ------------------------------------------------------------------------------------------------------------------
    def onSceneEndClose(self, caller, event):
        """     Called just after the scene is closed.    """''''''
        print("**Widget.onSceneEndClose(self, caller, event)")
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def on_mrmlScene_EndImport(self, caller, event):
        print("\n\n\n\n**Widget.on_mrmlScene_EndImport(self, caller, event)\n\n");

        # 01. Add **Logic Observer:       Search and Set nMS_Proxy_Landmark, with Observer onPointAdded
        if self.logic and self._parameterNode:
            # I. Before  updating the SingleTon ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
            wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

            self.logic.paramNodeUpdate_SearchSetModuleSingleton_ProxyNode_Landmarks(self._parameterNode)

            # III. After  updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
            self._parameterNode.EndModify(wasModified)

        # 02. Add **Widget Observer
        self.checkAdd_uiObserver_MarkupNodes()

    # ------------------------------------------------------------------------------------------------------------------
    def initializeParameterNode(self):
        """    Ensure parameter node exists and observed. """''''''
        # 01. Slicer-Initial: the SingleTon ParameterNode stores all user choices in param-values, node selections...
        #         so that when the scene is saved and reloaded, these settings are restored.
        self.setParameterNode(self.logic.getParameterNode())

        # 02. SL_Developer. Observe SeqBrowserProxy_Landmarks, onPointPositionDefined_Proxy
        self.checkAdd_uiObserver_MarkupNodes()

    # ------------------------------------------------------------------------------------------------------------------
    def getSafe_ProxyLandmarks_TargetSeqBrowser__paramNodeUpdate(self, nodeSeqBrowser):
        print("\t**Widget.getSafe_ProxyLandmarks_TargetSeqBrowser__paramNodeUpdate(self, nodeSeqBrowser), SL_Proxy")
        ''' SL_Notes: in function getSafe_*(), we initialize if the TargetNode did not exist! ''' ''''''
        # 01. Check if there is already a NodeReference saved in nodeSeqBrowser
        proxyNode_Landmarks_TargetSeqBrowser = self.logic.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser)
        if proxyNode_Landmarks_TargetSeqBrowser:
            nodeSeq_Landmarks = nodeSeqBrowser.GetSequenceNode(proxyNode_Landmarks_TargetSeqBrowser)
            if nodeSeq_Landmarks and nodeSeqBrowser.GetNumberOfItems() == nodeSeq_Landmarks.GetNumberOfDataNodes():
                return proxyNode_Landmarks_TargetSeqBrowser
            else:
                if nodeSeq_Landmarks:
                    print(f'\n\tnodeSeq_Landmarks.Number_DataNodes = {nodeSeq_Landmarks.GetNumberOfDataNodes()}\n')
                else:   print(f'type(nodeSeq_Landmarks) = {type(nodeSeq_Landmarks)}')

        # 02-A. Either ProxyNode or nodeSeq_Landmarks  Did Not exist: assign ModuleSingleton node_ProxyLandmark
        nMS_Proxy_Landmarks = self.logic.getSafe_ModuleSingleton_ProxyLandmarks__paramNodeUpdate()
        self.logic.setProxyNode_Landmarks_to_SeqBrowser(nodeSeqBrowser, nMS_Proxy_Landmarks)
        # 02-B. Safely Add Observer:  node_SeqBrowserProxy_Landmarks,  onPointPositionDefined_Proxy
        self.checkAdd_uiObserver_MarkupNodes()
        return nMS_Proxy_Landmarks

    # ------------------------------------------------------------------------------------------------------------------
    def checkAdd_uiObserver_MarkupNodes(self):
        ''' **Widget.checkAdd_uiObserver_MarkupNodes(self)   ''' ''''''
        # 01. Check if we need to AddObserver for newly created ModuleSingleton SeqBrowser_ProxyNode_Landmarks
        if (not self.uiObserverTag_LandmarkProxyNode_PointPositionDefined) and self._parameterNode:
            # 02. No ui_ObserverTag, check if nMS_SeqBrowserProxy_Landmarks is already created
            nMS_SeqBrowserProxy_Landmarks = self._parameterNode.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            if nMS_SeqBrowserProxy_Landmarks:
                # 03. nMS_SeqBrowserProxy_Landmarks Created but no  ui_Observer yet, let's add one
                self.uiObserverTag_LandmarkProxyNode_PointPositionDefined = nMS_SeqBrowserProxy_Landmarks.AddObserver( \
                    slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent, self.onPointPositionDefined_Proxy)

                nMS_SeqBrowserProxy_Landmarks.AddObserver(slicer.vtkMRMLMarkupsNode.PointStartInteractionEvent, \
                                                                self.onPointStartInteraction_Proxy)  # Start Drag Landmark
                nMS_SeqBrowserProxy_Landmarks.AddObserver(slicer.vtkMRMLMarkupsNode.PointEndInteractionEvent,
                                                                    self.onPointEndInteraction_Proxy) # Stop Drag Landmark
        # 02. Check add CurveControlPoint ClickEvent_Observer:  Tag not None (save to dict) as long as one Curve exist
        # 03. Set up DisplayNode    &   Attach Mouse Hover Observer
        list_SeqBrowserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
        for nodeSeqBrowser in list_SeqBrowserNodes:
            if not nodeSeqBrowser.GetID() in self.dict_uiObserverTag_onClickCurveControlPoint:
                nodeCurve_Left = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
                if nodeCurve_Left:
                    self.dict_uiObserverTag_onClickCurveControlPoint[nodeSeqBrowser.GetID()] = nodeCurve_Left.AddObserver( \
                        slicer.vtkMRMLMarkupsNode.PointStartInteractionEvent, self.onPointStartInteraction_LandmarkCurve)
                    self.logic.setVisibility_and_AddDisplayNodeObserver(nodeCurve_Left)

                nodeCurve_Right = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
                if nodeCurve_Right:
                    self.dict_uiObserverTag_onClickCurveControlPoint[nodeSeqBrowser.GetID()] = nodeCurve_Right.AddObserver( \
                        slicer.vtkMRMLMarkupsNode.PointStartInteractionEvent, self.onPointStartInteraction_LandmarkCurve)
                    self.logic.setVisibility_and_AddDisplayNodeObserver(nodeCurve_Right)

                nodeCurve_SpinalCord = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_SpinalCord)
                if nodeCurve_SpinalCord:
                    self.dict_uiObserverTag_onClickCurveControlPoint[nodeSeqBrowser.GetID()] = nodeCurve_SpinalCord.AddObserver( \
                        slicer.vtkMRMLMarkupsNode.PointStartInteractionEvent, self.onPointStartInteraction_LandmarkCurve)
                    self.logic.setVisibility_and_AddDisplayNodeObserver(nodeCurve_SpinalCord)

    # ------------------------------------------------------------------------------------------------------------------
    def setParameterNode(self, inputParameterNode):
        """    SL_Notes:  Set and observe the SingleTon ParameterNode.
                  Observation is needed because when ParameterNode is changed then the GUI must be updated immediately.
        """''''''
        print("**Widget.setParameterNode(self, inputParameterNode)")
        if inputParameterNode:
            if not inputParameterNode.IsSingleton():
                raise ValueError(f'SL__Allert! \tinputParameterNode = \n{inputParameterNode.__str__()}')
            self.logic.setDefaultParameters(inputParameterNode)

        # 01. Unobserve previously selected SingleTon ParameterNode;
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 02. Set new SingleTon ParameterNode and  Add an observer to the newly selected
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 03. Initial GUI update; need to do this GUI update whenever there is a change from the SingleTon ParameterNode
        self.updateGUIFromParameterNode()

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section I:  ShortCut              ===========================================
    # ------------------------------------------------------------------------------------------------------------------
    def initializeShortCut(self):
        print("**Widget.initializeShortCut(self), \tSL_Developer"); test = 0; test += 1
        # 01. Summary of the ShortCut
        listTuplePair_strQKeySequence_CallBack = [
            ("left",    lambda: self.onShortCutKeyBoardClicked_Left()),
            ("right",   lambda: self.onShortCutKeyBoardClicked_Right()),
        ]
        # 02. Activate the ShortCut
        for (strQKeySequence, callback) in listTuplePair_strQKeySequence_CallBack:
            shortcut = qt.QShortcut(qt.QKeySequence(strQKeySequence), slicer.util.mainWindow())
            shortcut.connect("activated()", callback)

    # ------------------------------------------------------------------------------------------------------------------
    def checkLastControlPoint_And_RemoveNonPositionDefined(self, nodeSeqBrowser_Selected):
        # 01. Remove ControlPoint if applicable (not PositionDefined)
        proxyNode_Landmark = nodeSeqBrowser_Selected.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
        if proxyNode_Landmark:
            num_ControlPoint = proxyNode_Landmark.GetNumberOfControlPoints()
            if num_ControlPoint > 0 and proxyNode_Landmark.GetNthControlPointPositionStatus(num_ControlPoint - 1)  \
                        != slicer.vtkMRMLMarkupsNode.PositionDefined:
                # 01-A. Remove Sequential   Preview ControlPoint
                nodePointList_Sequential_curFrame = self.logic.obtainDataNode_CurSelected(nodeSeqBrowser_Selected, proxyNode_Landmark)
                if nodePointList_Sequential_curFrame.GetNumberOfControlPoints() == proxyNode_Landmark.GetNumberOfControlPoints():
                    nodePointList_Sequential_curFrame.RemoveNthControlPoint(num_ControlPoint - 1)
                # 01-B. Remove proxy        Preview ControlPoint
                proxyNode_Landmark.RemoveNthControlPoint(num_ControlPoint - 1)

                        
    def onShortCutKeyBoardClicked_Left(self):
        ''' **Widget.onShortCutKeyBoardClicked_Left() ''' ''''''
        # 00-A. Check if ModuleSingleton has been initialized
        if self._parameterNode is None:            return
        # 00-B. Check the Validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected or nodeSeqBrowser_Selected.GetNumberOfItems() == 0:
            return
        # 01. Remove Preview ControlPoint if applicable (PlaceMode)
        self.checkLastControlPoint_And_RemoveNonPositionDefined(nodeSeqBrowser_Selected)
        # 02. LogicUpdate:   nodeSeqBrowser's  Current-SelectedItemNumber
        idx_preFrame = self.logic.obtainSafe_idxPreFrame_from_TargetSeqBrowser(nodeSeqBrowser_Selected)
        self.logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(idx_preFrame)
        print(f'**Widget.onShortCutKeyBoardClicked_Left(),\tidx_preFrame = {idx_preFrame}')
        # 03. uiUpdate
        self._updatingGUIFromParameterNode = True   # I. Open-Brace:  Avoid updateParameterNodeFromGUI__ (infinite loop)
        self.uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex()
        self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;

    # ------------------------------------------------------------------------------------------------------------------
    def onShortCutKeyBoardClicked_Right(self):
        ''' **Widget.onShortCutKeyBoardClicked_Right() ''' ''''''
        # 00-A. Check if ModuleSingleton has been initialized
        if self._parameterNode is None:            return
        # 00-B. Check the Validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected or nodeSeqBrowser_Selected.GetNumberOfItems() == 0:
            return
        # 01. Remove Preview ControlPoint if applicable (PlaceMode)
        self.checkLastControlPoint_And_RemoveNonPositionDefined(nodeSeqBrowser_Selected)
        # 02. LogicUpdate:   nodeSeqBrowser's  Current-SelectedItemNumber
        idx_nextFrame = self.logic.obtainSafe_idxNextFrame_from_TargetSeqBrowser(nodeSeqBrowser_Selected)
        print(f'**Widget.onShortCutKeyBoardClicked_Right(),\tidx_nextFrame = {idx_nextFrame}')
        self.logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(idx_nextFrame)
        # 03. uiUpdate
        self._updatingGUIFromParameterNode = True   # I. Open-Brace:  Avoid updateParameterNodeFromGUI__ (infinite loop)
        self.uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex()
        self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section II:  get, set, obtain                ================================
    # ------------------------------------------------------------------------------------------------------------------
    def getSelectedItemNumber_FromGUI_Slider(self):
        idx_CurSeqBrowser_SelectedItemNumber = self.ui.slider_SeqFrame.value - INT_SliderFrameIndex_Min
        return idx_CurSeqBrowser_SelectedItemNumber

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def obtain_uiTargetLabel_from_LabelPrefix(self, str_TargetLandmarkPrefix, uiLabel_IJ_Left, uiLabel_IJ_Right):
        #  Determine uiTargetLabel based on str_TargetLandmarkPrefix, either uiLabel_IJ_Left or uiLabel_IJ_Right
        if str_TargetLandmarkPrefix == STR_ControlPointLabelPrefix_Left:        uiTargetLabel = uiLabel_IJ_Left
        elif str_TargetLandmarkPrefix == STR_ControlPointLabelPrefix_Right:     uiTargetLabel = uiLabel_IJ_Right
        else:
            uiLabel_IJ_Left.setText(f'(Wrong LabelPrefix = {str_TargetLandmarkPrefix})')
            uiLabel_IJ_Right.setText(f'(Wrong LabelPrefix = {str_TargetLandmarkPrefix})')
            raise ValueError(f'\n\n\t\t SL_Alert! Wrong LabelPrefix = {str_TargetLandmarkPrefix}\n')
        return uiTargetLabel

    def obtain_uiTargetLabel_from_WholeLabel(self, nodePointList_TargetFrame, idx_ControlPoint, uiLabel_IJ_Left, uiLabel_IJ_Right):
        #  Determine uiTargetLabel based on str_ControPoint_Label, either uiLabel_IJ_Left or uiLabel_IJ_Right
        str_ControPoint_Label = nodePointList_TargetFrame.GetNthControlPointLabel(idx_ControlPoint)
        if STR_ControlPointLabelPrefix_Left in str_ControPoint_Label:
            uiTargetLabel = uiLabel_IJ_Left;   str_TargetLandmarkPrefix = STR_ControlPointLabelPrefix_Left
        elif STR_ControlPointLabelPrefix_Right in str_ControPoint_Label:
            uiTargetLabel = uiLabel_IJ_Right;  str_TargetLandmarkPrefix = STR_ControlPointLabelPrefix_Right
        else:
            uiLabel_IJ_Left.setText(f'(Wrong label = {str_ControPoint_Label})')
            uiLabel_IJ_Right.setText(f'(Wrong label = {str_ControPoint_Label})')
            raise ValueError(f'\n\n\t\t SL_Alert! Wrong label = {str_ControPoint_Label}\n')
        return uiTargetLabel, str_TargetLandmarkPrefix

    # ------------------------------------------------------------------------------------------------------------------

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section III:  updateGUIFromParameterNode__  &    Slots   that call uiUpdate =
    # ------------------------------------------------------------------------------------------------------------------
    def updateGUIFromParameterNode(self, caller=None, event=None):
        """   This method is called whenever parameter node is changed.
              The module GUI is updated to show the current state of the parameter node.    """''''''
        # 00. Check self._updatingGUIFromParameterNode to prevent from GUI changes
        #       (it could cause infinite loop:  GUI change -> UpdateParamNode -> Update GUI -> UpdateParamNode)
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # I. Open-Brace:  Make sure GUI changes do not call updateParameterNodeFromGUI__ (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True
        # --------------------------------------------------------------------------------------------------------------
        # II. SL_Developer, C:  In-Brace,   Update UI widgets ()
        print("**Widget.updateGUIFromParameterNode(self, caller=None, event=None), \tSL_Developer")
        #   II-01. Update Values of   Node-Selectors (qMRMLNodeComboBox)
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        self.ui.sequenceSelector.setCurrentNode(nodeSeqBrowser_Selected)
        #   II-02. Update Status of  slider_SeqFrame, and label_FrameIndex:    QLabel,     Sliders (ctkSliderWidget)
        self.uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(nodeSeqBrowser_Selected)
        #   II-03. Update Status of  landmarkCollapsibleButton:                QCheckBox (is Negative Frame)
        self.uiUpdate_CollapsibleButton_LaminaeLandmarks(nodeSeqBrowser_Selected)
        # --------------------------------------------------------------------------------------------------------------
        # III. Close-Brace: All the GUI updates are done;
        self._updatingGUIFromParameterNode = False

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def onSliderFrameIndex_ValueChanged(self, caller=None, event=None):
        ''' SL_Notes:   Not UserOnly function, can be called when a target_ControlPoint is selected!    ''' ''''''
        # 00. Check Singleton ParameterNode: in case of enter() or onSceneStartClose()
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # 01. LogicUpdate:   nodeSeqBrowser's  Current-SelectedItemNumber
        idx_CurFrame = self.getSelectedItemNumber_FromGUI_Slider()
        self.logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(idx_CurFrame)
        print(f'\t**Widget.onSliderFrameIndex_ValueChanged,\tidx_CurFrame = {idx_CurFrame}')

        # 02. uiUpdate:      LandmarkPositionLabels
        self._updatingGUIFromParameterNode = True  # I. Open-Brace:  Avoid updateParameterNodeFromGUI__ (infinite loop)
        self.uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex() # II. In-Brace: uiUpdate
        self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;

    # ------------------------------------------------------------------------------------------------------------------
    def onSelectedNodeChanged(self, node_NewActiveBrowser=None, event=None):
        ''' SL_Notes:   Not UserOnly function, can be called when a target_ControlPoint is selected!    ''' ''''''
        print(f"\nBeginning of **Widget.onSelectedNodeChanged():   \tnode_NewActiveBrowser ="
              f" {node_NewActiveBrowser.GetID() if node_NewActiveBrowser else type(node_NewActiveBrowser)}")
        # 00-A. Check Singleton ParameterNode: important test for every NodeChange Slot, in case of onSceneStartClose()
        #       Check _updatingGUIFromParameterNode:  avoid bugs introduced by Slicer (PointAdded, PointPositionDefined)
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        # 00-B. Check the validity of node_NewActiveBrowser
        if not node_NewActiveBrowser:
            return
        # print('1', self.debugOnly_Get_isNegativeFrame())

        # 01. LogicUpdate
        # I. OpenBrace: To avoid Slicer AddPointEvent -> PointPositionDefinedEvent, use flag isSwitchingSeqBrowser
        self.logic.set_isSwitchingSeqBrowser(True)
        # --------------------------------------------------------------------------------------------------------------
        # II-01-A. Stop All SeqBrowsers' Sequence_Landmark SaveChanges SetFalse:  prevent Incorrect Landmark Change
        self.logic.setAllSeqBrowser_SeqLandmark_SaveChanges_False__EmptyProxyNode()
        # II-01-B. Update the SingleTon ParameterNode, so that you can get the correct nodeSeqBrowser in #03
        self.updateParameterNodeFromGUI__Set_RefRoleNodeID(STR_SeqBrowserNode_RefRole_Selected, node_NewActiveBrowser.GetID())
        # II-01-C. Update ProxyNode_Landmark's Visibility
        self.logic.updateVisibility_ProxyNode_Landmark(node_NewActiveBrowser)
        # II-01-D. Update Visibility of all Landmark_Curves
        self.logic.updateVisibility_LandmarkCurves_ShowOnlySelectedSeqBrowser()
        # --------------------------------------------------------------------------------------------------------------
        # III. CloseBrace: To avoid Slicer AddPointEvent -> PointPositionDefinedEvent, use flag isSwitchingSeqBrowser
        self.logic.set_isSwitchingSeqBrowser(False)

        # 02. uiUpdate:     update  slider_SeqFrame  &   landmarkCollapsibleButton
        if self.parent.isEntered:
            # I. Open-Brace:  Make sure GUI changes do not call updateParameterNodeFromGUI__ (it could cause infinite loop)
            self._updatingGUIFromParameterNode = True
            # --------------------------------------------------------------------------------------------------------------
            #   II-02-A. Re-Set sequenceSelector, just in case the Signal sender is Sequences.toolBar()
            self.ui.sequenceSelector.setCurrentNode(node_NewActiveBrowser)
            #   II-02-B. Re-Set modules.sequences active SeqBrowser, just in case the Signal sender is Laminae-Labeling
            slicer.modules.sequences.widgetRepresentation().setActiveBrowserNode(node_NewActiveBrowser)
            #   II-02-C. Push Slicer Screen refresh before uiUpdate
            self.uiUpdate_PushSlicerScreenUpdate_by_ShakeTargetSeqBrowser(node_NewActiveBrowser)
            #   II-02-D. Reset CollapsibleButton First before uiUpdate
            self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton()
            #   II-02-E. Start uiUpdate
            self.uiUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(node_NewActiveBrowser)
            # --------------------------------------------------------------------------------------------------------------
            # III. Close-Brace: All the GUI updates are done;
            self._updatingGUIFromParameterNode = False

    # ------------------------------------------------------------------------------------------------------------------
    def debugOnly_Get_isNegativeFrame(self, idx_TargetFrame= 440):
        nodeSeqBrowser_Target = slicer.util.getNode('SeqBrowser_1__S_LT__snS')
        if self.ui_HasLandmarks_uiCollapsibleButtonUpdateNeeded(nodeSeqBrowser_Target):
            proxyNode_Landmark = slicer.util.getNode('Proxy_pList_Landmarks')
            nodeSeq_Target = nodeSeqBrowser_Target.GetSequenceNode(proxyNode_Landmark)
            nodePointList_Sequential_curFrame = nodeSeq_Target.GetNthDataNode(idx_TargetFrame)
            isNegative = nodePointList_Sequential_curFrame.GetAttribute(STR_AttriName_NodePointList_isNegativeFrame)
            return f'{nodeSeqBrowser_Target.GetID()}    \tidx_TargetFrame {idx_TargetFrame}  \t isNegative =  {isNegative})'
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def onPointPositionDefined_Proxy(self, proxyNode_Landmark=None, event=None):
        # 00-A. Check Singleton ParameterNode: important test for every NodeChange Slot, in case of onSceneStartClose()
        #       Check _updatingGUIFromParameterNode:  avoid bugs introduced by Slicer (PointAdded, PointPositionDefined)
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        # 00-B. Check if there is a real ControlPoint dropped manually; ProxyNode-Seq-AutoUpdate can also trigger event
        num_ControlPoints = proxyNode_Landmark.GetNumberOfControlPoints()
        print(f"\n\t**Widget.onPointPositionDefined_Proxy(self), \tnum_ControlPoints = {num_ControlPoints}")
        if num_ControlPoints == 0:
            # This means the event was triggered by ProxyNode-Seq-AutoUpdate, no need to continue
            return

        # 01. SetFalse to Attribute isNegative CheckBox value to Attribute
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        nodePointList_Sequential_curFrame = self.logic.obtainDataNode_CurSelected(nodeSeqBrowser_Selected, proxyNode_Landmark)
        if self.logic.get_isSwitchingSeqBrowser():
            # SL_Notes: during onSelectedNodeChanged() step SetFalse_Empty, Slicer will AddPoint
            #               to proxyNode and lead to PointPositionDefinedEvent, thus here.
            print(f'\n\nisSwitchingSeqBrowser !! SwitchingSeqBrowser!! SwitchingSeqBrowser!!!\n\n')
            proxyNode_Landmark.RemoveAllControlPoints()
        else:
            #       01-A.   Save Attribute for proxyNode_Landmark
            proxyNode_Landmark.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, STR_FALSE)
            #       01-B.   Save Attribute for Sequential_nodePointList
            nodePointList_Sequential_curFrame.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, STR_FALSE)

        # 02. Remove the OldExisted PositionDefined Landmarks (ControlPoints) to let the latest be the Landmark
        # 02-A. Remove from proxyNode_Landmark:
        self.removeOldExistingLandmarks_from_TargetPointList(proxyNode_Landmark)
        # 02-B. Remove from Sequential nodePointList: same procedure, just in case the SaveChanges is not triggered!
        self.removeOldExistingLandmarks_from_TargetPointList(nodePointList_Sequential_curFrame, 'SL__Sequential')

        # # 03. If isUserLabeling, we need to add the same ControlPoint to corresponding LandmarkCurve!
        if self.logic.isUserLabeling_InteractionSingleton_PlaceMode():
            self.logic.updateCurves_FrameLandmarks__on_ProxyControlPointUpdate(nodeSeqBrowser_Selected, proxyNode_Landmark)

        # 04. Update uiLabel_LandmarkPosition_curFrame for the newly added ControlPoint
        if self.parent.isEntered:
            self._updatingGUIFromParameterNode = True  # I. Open-Brace:  Avoid updateParameterNodeFromGUI_(InfiniteLoop)
            self.uiUpdate_LandmarkPositionPanel_TargetFrame(strFrameType=STR_FRAME_TYPE_CURRENT)# II. In-Brace: uiUpdate
            self._updatingGUIFromParameterNode = False # III. Close-Brace: All the GUI updates are done;

    # ------------------------------------------------------------------------------------------------------------------
    def removeOldExistingLandmarks_from_TargetPointList(self, nodePointList_Target, strNote_PointListType='SL__Proxy'):
        # 00. Check num_ControlPoints
        num_ControlPoints = nodePointList_Target.GetNumberOfControlPoints()
        if num_ControlPoints < 0:
            raise ValueError(f'SL_Alert! Should not be called, num_ControlPoints = {num_ControlPoints}')

        # 01. Find the most recent idx_NewlyAdded_PositionDefined
        idx_LastControlPoint = num_ControlPoints - 1  # Index starts from 0
        idx_NewlyAdded_PositionDefined = idx_LastControlPoint
        while idx_NewlyAdded_PositionDefined >= 0:
            # If in the persistent PlaceMode, the we skip the newly added Undefined ControlPoint!
            if nodePointList_Target.GetNthControlPointPositionStatus(idx_NewlyAdded_PositionDefined)  \
                        == slicer.vtkMRMLMarkupsNode.PositionDefined:                break
            else:
                idx_NewlyAdded_PositionDefined = idx_NewlyAdded_PositionDefined - 1
        strLabel_NewlyAddedControlPoint = nodePointList_Target.GetNthControlPointLabel(idx_NewlyAdded_PositionDefined)

        # 02. Traverse in descending order, because idx changes during removing
        idx_Start = idx_NewlyAdded_PositionDefined - 1  # This minus 1 is to avoid ControlPoint_OnGoing
        idx_End = 0 - 1  # Stop at 0, minus 1 because Python open right brace
        for idx_ControlPoint in range(idx_Start, idx_End, -1):  # -1 for descending operation of idx_ControlPoint
            if nodePointList_Target.GetNthControlPointLabel(idx_ControlPoint) == strLabel_NewlyAddedControlPoint:
                if nodePointList_Target.GetNthControlPointPositionStatus(idx_LastControlPoint) \
                            == slicer.vtkMRMLMarkupsNode.PositionDefined:
                    # 02. Found the old existing ControlPoint, remove this ControlPoint
                    nodePointList_Target.RemoveNthControlPoint(idx_ControlPoint)
                    print(f'\t\tRemoved idx_ControlPoint = {idx_ControlPoint}, PointList_NodeType = {strNote_PointListType}\n\n')

    # ------------------------------------------------------------------------------------------------------------------
    def onPointStartInteraction_Proxy(self, proxyNode_Landmark=None, event=None):
        print("\t**Widget.PointStartInteractionEvent(self, nodePointList, event), SL_Proxy"); test = 0; test += 1
        # 00-A. If not this module, no need to uiUpdate
        if not self.parent.isEntered:
            return
        # 00-B. Check Singleton ParameterNode: important test for every NodeChange Slot, in case of onSceneStartClose()
        #       Check _updatingGUIFromParameterNode:  avoid bugs introduced by Slicer (PointAdded, PointPositionDefined)
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        # 00-C. Check the validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected or nodeSeqBrowser_Selected.GetNumberOfItems() == 0:
            # Invalid SeqBrowser_Selected or No recorded data in nodeSeqBrowser_Selected:   no need to continue
            return
        # 00-D. Check the validity of Seq_Landmark from SeqBrowser_Selected
        node_ProxyLandmarks_SelectedSeqBrowser = self.logic.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser_Selected)
        if not node_ProxyLandmarks_SelectedSeqBrowser:
            # SL_Note:  Drop-Landmark button was not triggered, no need to continue
            return

        # 01. Set SeqBrowser Sequence_Landmarks' SaveChanges to Positive
        nodeSeq_Landmarks = nodeSeqBrowser_Selected.GetSequenceNode(node_ProxyLandmarks_SelectedSeqBrowser)
        nodeSeqBrowser_Selected.SetSaveChanges(nodeSeq_Landmarks, True)

        # I. Open-Brace:  Make sure GUI changes do not call updateParameterNodeFromGUI__ (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True
        # --------------------------------------------------------------------------------------------------------------
        #   II-02. Set attribute STR_AttriName__Idx_ControlPoint_MousePicked     &   uiUpdate
        node_CrossHair = slicer.util.getNode(STR_NodeName_CrossHair)
        if node_CrossHair:
            #   II-02-A. Get current MousePosition_World_RAS
            list_RAS_World_Mouse = [0, 0, 0]
            node_CrossHair.GetCursorPositionRAS(list_RAS_World_Mouse)
            #   II-02-B. Determine the idx_ControlPoint_MousePicked, and set attribute!
            idx_ControlPoint_MousePicked = proxyNode_Landmark.GetClosestControlPointIndexToPositionWorld(list_RAS_World_Mouse)
            proxyNode_Landmark.SetAttribute(STR_AttriName__Idx_ControlPoint_MousePicked, str(idx_ControlPoint_MousePicked))
            #   II-02-C. Determine and Update the  uiLabel's  background
            str_ControPoint_MousePicked = proxyNode_Landmark.GetNthControlPointLabel(idx_ControlPoint_MousePicked)
            if STR_ControlPointLabelPrefix_Left in str_ControPoint_MousePicked:
                self.ui.label__Left_IJ__curFrame.setStyleSheet(STR_QLabel_StyleSheet_onLandmarkMouseDrag)
            elif STR_ControlPointLabelPrefix_Right in str_ControPoint_MousePicked:
                self.ui.label__Right_IJ__curFrame.setStyleSheet(STR_QLabel_StyleSheet_onLandmarkMouseDrag)
            else:
                raise ValueError(f'\n\n\t\t SL_Alert! Wrong label = {str_ControPoint_MousePicked}\n')
        else:
            raise ValueError(f'\n\n\t\t SL_Alert! Not able to find node {STR_NodeName_CrossHair}\n')
        # --------------------------------------------------------------------------------------------------------------
        # III. Close-Brace: All the GUI updates are done;
        self._updatingGUIFromParameterNode = False

    # ------------------------------------------------------------------------------------------------------------------
    def onPointEndInteraction_Proxy(self, proxyNode_Landmark=None, event=None):
        print("\t**Widget.onPointEndInteraction_Proxy(self, nodePointList, event), SL_Proxy"); test = 0; test += 1
        # 00-A. Check Singleton ParameterNode: important test for every NodeChange Slot, in case of onSceneStartClose()
        #       Check _updatingGUIFromParameterNode:  avoid bugs introduced by Slicer (PointAdded, PointPositionDefined)
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # 01. Update the Landmark_Curves
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        self.logic.updateCurves_FrameLandmarks__on_ProxyControlPointUpdate(nodeSeqBrowser_Selected, proxyNode_Landmark)

        # 02. If not this module, no need to uiUpdate
        if not self.parent.isEntered:
            return

        # I. Open-Brace:  Make sure GUI changes do not call updateParameterNodeFromGUI__ (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True
        # --------------------------------------------------------------------------------------------------------------
        #   II-03. Update Landmark-Position
        self.uiUpdate_LandmarkPositionPanel_TargetFrame(STR_FRAME_TYPE_CURRENT)
        #   II-04. Recover BackgroundColor of the Label corresponds to MousePicked ControlPoint
        idx_ControlPoint_MousePicked = int(proxyNode_Landmark.GetAttribute(STR_AttriName__Idx_ControlPoint_MousePicked))
        str_ControPoint_MousePicked = proxyNode_Landmark.GetNthControlPointLabel(idx_ControlPoint_MousePicked)
        if STR_ControlPointLabelPrefix_Left in str_ControPoint_MousePicked:
            self.ui.label__Left_IJ__curFrame.setStyleSheet('')
        elif STR_ControlPointLabelPrefix_Right in str_ControPoint_MousePicked:
            self.ui.label__Right_IJ__curFrame.setStyleSheet('')
        else:
            raise ValueError(f'\n\n\t\t SL_Alert! Wrong label = {str_ControPoint_MousePicked}\n')
        # --------------------------------------------------------------------------------------------------------------
        # III. Close-Brace: All the GUI updates are done;
        self._updatingGUIFromParameterNode = False
    
    # ------------------------------------------------------------------------------------------------------------------
    def onPointStartInteraction_LandmarkCurve(self, nodeCurve_Caller=None, event=None):
        print("\t**Widget.onPointStartInteraction_LandmarkCurve(self, nodeCurve_Target, event), SL_Proxy"); 
        nodeSeqBrowser_Caller = nodeCurve_Caller.GetNodeReference(STR_SeqBrowserNode_RefRole_Parent)
        # 01. Update Selected SeqBrowser
        self.onSelectedNodeChanged(nodeSeqBrowser_Caller)

        # 02. Get Selected idx_TargetControlPoint:  cannot use node_CrossHair because it does not work well in 3D
        nodeDiaplay_CallerCurve = nodeCurve_Caller.GetDisplayNode()
        int_ActiveComponentType = nodeDiaplay_CallerCurve.GetActiveComponentType()
        if int_ActiveComponentType == slicer.vtkMRMLMarkupsDisplayNode.ComponentControlPoint:
            idx_ControlPoint_Target = nodeDiaplay_CallerCurve.GetActiveComponentIndex()
        else:   raise ValueError(f'SL_Alert! int_ActiveComponentType = {int_ActiveComponentType}')

        # 03. Determine the idxFrame_Target based on ControlPoint's label
        strLabel_ControlPoint_MousePiced = nodeCurve_Caller.GetNthControlPointLabel(idx_ControlPoint_Target)
        _, idxFrame_Target =self.logic.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_ControlPoint_MousePiced)

        print(f'\n\t Switching to idxFrame_Target = {idxFrame_Target}\n')
        # 04. Set and update  nodeSeqBrowser_Target.SetSelectedItem:     MousePicked ControlPoint
        #       04-A. LogicUpdate:   nodeSeqBrowser's  Current-SelectedItemNumber
        self.logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(idxFrame_Target)
        print(f'\t**Widget.onPointStartInteraction_LandmarkCurve,\tidx_CurFrame = {idxFrame_Target}')
        #       04-B. uiUpdate:      LandmarkPositionLabels
        self._updatingGUIFromParameterNode = True  # I. Open-Brace:  Avoid updateParameterNodeFromGUI__ (infinite loop)
        self.uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex()  # II. In-Brace: uiUpdate
        self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;


    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # -----------        Section III-02:     Sub-Functions called by updateGUIFromParameterNode__      -----------------
    # ----- 1. All sub-functions starts with uiUpdate               ----------------------------------------------------
    # ----- 2. All uiUpdate functions                        canNOT     set     Self._updatingGUIFromParameterNode  ----
    # ----- 3. The superior function who call uiUpdate function MUST    set     Self._updatingGUIFromParameterNode  ----
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(self, nodeSeqBrowser_Selected):
        ''' **Widget.uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(self, nodeSeqBrowser_Selected)   ''' ''''''
        if nodeSeqBrowser_Selected:
            str_CurSeqBrowser_ID = 'nodeSeqBrowser_Selected.GetID() = ' + nodeSeqBrowser_Selected.GetID()
            str_NumberOfItems = '.GetNumberOfItems() = ' + str(nodeSeqBrowser_Selected.GetNumberOfItems())
            str_idxFrame =  f', \tidxFrame = {self.logic.obtain_idxSliderCurFrame_from_TargetSeqBrowser(nodeSeqBrowser_Selected)}'
        else:
            str_CurSeqBrowser_ID = 'CurSeqBrowser.GetID() = ' + str(type(nodeSeqBrowser_Selected))
            str_NumberOfItems = ''
            str_idxFrame = ''
        print(f"\t**Widget.uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(), {str_CurSeqBrowser_ID}, {str_NumberOfItems}{str_idxFrame}")

        if nodeSeqBrowser_Selected and nodeSeqBrowser_Selected.GetNumberOfItems() > 0:
            self.ui.slider_SeqFrame.enabled = True
            self.ui.slider_SeqFrame.minimum = INT_SliderFrameIndex_Min
            self.ui.slider_SeqFrame.maximum = nodeSeqBrowser_Selected.GetNumberOfItems()
            self.ui.slider_SeqFrame.value   = self.logic.obtain_idxSliderCurFrame_from_TargetSeqBrowser(nodeSeqBrowser_Selected)
            self.ui.label_FrameIndex.setText(str(self.ui.slider_SeqFrame.value))
        else:
            # No SequenceBrowser_Node available, so we disable the slider_SeqFrame, and set label_FrameIndex 'N/A'
            self.ui.slider_SeqFrame.enabled = False
            self.ui.slider_SeqFrame.minimum = INT_SliderFrameIndex_Min
            self.ui.slider_SeqFrame.maximum = INT_FRAME_INDEX_SLIDER_DEFAULT_MAX
            self.ui.slider_SeqFrame.value   = INT_FRAME_INDEX_SLIDER_DEFAULT
            self.ui.label_FrameIndex.setText('N/A')

    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_CollapsibleButton_LaminaeLandmarks(self, node_NewActiveBrowser):
        if node_NewActiveBrowser:
            str_CurSeqBrowser_ID = 'node_NewActiveBrowser.GetID() = ' + node_NewActiveBrowser.GetID()
            str_NumberOfItems = 'NumberOfItems() = ' + str(node_NewActiveBrowser.GetNumberOfItems())
        else:
            str_CurSeqBrowser_ID = 'node_NewActiveBrowser.GetID() = ' + str(type(node_NewActiveBrowser))
            str_NumberOfItems = ''
        print(f"\t**Widget.uiUpdate_CollapsibleButton_LaminaeLandmarks(),  {str_CurSeqBrowser_ID}, {str_NumberOfItems}")

        if node_NewActiveBrowser and node_NewActiveBrowser.GetNumberOfItems() > 0:
            self.ui.landmarkCollapsibleButton.enabled = True  # 00. Enable the whole CollapsibleButton
            self.uiUpdate_All_LandmarkPositionPanels_inCollapsibleButton()      # 01. Update All LandmarkPositionPanels
        else:
            self.ui.landmarkCollapsibleButton.enabled = False  # 00. Disable the whole CollapsibleButton
            self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton()  # 01. SetDefault LandmarkPositionPanels

    # -------------------------------------------------------------------------------------------------------------------
    def uiUpdate_All_LandmarkPositionPanels_inCollapsibleButton(self):
        self.uiUpdate_LandmarkPositionPanel_TargetFrame(strFrameType=STR_FRAME_TYPE_PREVIOUS)
        self.uiUpdate_LandmarkPositionPanel_TargetFrame(strFrameType=STR_FRAME_TYPE_CURRENT)
        self.uiUpdate_LandmarkPositionPanel_TargetFrame(strFrameType=STR_FRAME_TYPE_NEXT)

    def uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton(self):
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Left_IJ__curFrame)
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Left_IJ__preFrame)
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Left_IJ__nextFrame)
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Right_IJ__curFrame)
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Right_IJ__preFrame)
        self.uiSetDefault_LandmarkPosition_OneLabelOnly(self.ui.label_Tuple__Right_IJ__nextFrame)
        self.ui.checkBox_Negative_curFrame.checked = False
        self.ui.checkBox_Negative_preFrame.checked = False
        self.ui.checkBox_Negative_nextFrame.checked = False
        self.ui.pushButton_Output_SeqNumpyLandmarks.enabled = False

    def uiSetDefault_LandmarkPosition_OneLabelOnly(self, uiTargetLabel):
        uiTargetLabel.setText(f'(N/A,\tN/A)')
        uiTargetLabel.setStyleSheet('')
    def uiSetNegative_LandmarkPosition_OneLabelOnly(self, uiTargetLabel):
        uiTargetLabel.setText(f'(-1,\t-1)')
        uiTargetLabel.setStyleSheet('')

    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_LandmarkPositionLabel_OneControlPoint(self, nodePointList_TargetFrame, idx_ControlPoint,
            tuple_ValidImageShape, mat4x4_World_2_SonixTablet, mat_RASToIJK, uiTargetLabel):
        ''' **Widget.uiUpdate_LandmarkPositionLabel_OneControlPoint() ''' ''''''
        # Update uiTargetLabel using the idx_ControlPoint
        num_ControlPoints = nodePointList_TargetFrame.GetNumberOfControlPoints()
        if num_ControlPoints <= 0 or idx_ControlPoint < 0 or idx_ControlPoint >= num_ControlPoints:
            uiTargetLabel.setText(f'(num={num_ControlPoints},\tidx={idx_ControlPoint})')
            raise ValueError(f'\n\n\t\tSL_Alert!! num = {num_ControlPoints},\tidx = {idx_ControlPoint}\n\n')
        else:
            # 01. Get   RAS_ControlPoint:     vtkVec3d_RAS_World Coordinates
            vtkVec3d_RAS_World = nodePointList_TargetFrame.GetNthControlPointPositionVector(idx_ControlPoint)
            # 02. Get tuple4D_IJK_SonixTablet;    SL_Note: image IJK_Coords stay in SonixTablet_Coordinates
            tuple4D_IJK_SonixTablet = self.logic.obtain__IJK_SonixTablet__from__RAS_World(vtkVec3d_RAS_World,
                                                                                mat4x4_World_2_SonixTablet, mat_RASToIJK)
            # 03. Check if tuple4D_IJK_SonixTablet out of Frame using tuple_ValidImageShape
            str_LabelStyleSheet = ''
            str_I_Col = str(round(tuple4D_IJK_SonixTablet[0]))
            str_J_Row = str(round(tuple4D_IJK_SonixTablet[1]))
            if tuple4D_IJK_SonixTablet[0] < 0 or tuple4D_IJK_SonixTablet[0] >=  tuple_ValidImageShape[0]:
                str_I_Col = 'Out-of-Frame';     str_LabelStyleSheet = STR_QLabel_StyleSheet_Allert
            if tuple4D_IJK_SonixTablet[1] < 0 or tuple4D_IJK_SonixTablet[1] >= tuple_ValidImageShape[1]:
                str_J_Row = 'Out-of-Frame';     str_LabelStyleSheet = STR_QLabel_StyleSheet_Allert

            # 04. Update uiTargetLabel based on ControlPoint_Label
            uiTargetLabel.setText(f'({str_I_Col},\t{str_J_Row})')
            uiTargetLabel.setStyleSheet(str_LabelStyleSheet)

    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_LandmarkPositionPanel_TargetFrame(self, strFrameType = STR_FRAME_TYPE_CURRENT):
        ''' **Widget.uiUpdate_LandmarkPositionPanel_TargetFrame() ''' ''''''
        # 00-A. No need to update if the SeqBrowser_Selected does not contain the sequence of Landmarks
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if self.ui_HasLandmarks_uiCollapsibleButtonUpdateNeeded(nodeSeqBrowser_Selected) == False:
            return
        # 00-B. Check if nodeSeqBrowser_Selected.GetSelectedItemNumber() is Valid
        idx_curFrame = nodeSeqBrowser_Selected.GetSelectedItemNumber()
        if idx_curFrame < 0 or idx_curFrame >= nodeSeqBrowser_Selected.GetNumberOfItems():
            raise ValueError(f'SL_Alert! Incorrect nodeSeqBrowser_Selected.GetSelectedItemNumber() = {idx_curFrame}')
            return

        # 01. Enable PushButton_OutputLandmarks
        self.ui.pushButton_Output_SeqNumpyLandmarks.enabled = True

        # 02. Determine TargetFrame:    uiLabel_IJ_Left, uiLabel_IJ_Right, idx_TargetFrame
        if strFrameType == STR_FRAME_TYPE_CURRENT:
            uiLabel_IJ_Left     = self.ui.label_Tuple__Left_IJ__curFrame
            uiLabel_IJ_Right    = self.ui.label_Tuple__Right_IJ__curFrame
            uiNegativeCheckBox_TargetFrame = self.ui.checkBox_Negative_curFrame
            idx_TargetFrame     = nodeSeqBrowser_Selected.GetSelectedItemNumber()       # curFrame
        elif strFrameType == STR_FRAME_TYPE_PREVIOUS:
            uiLabel_IJ_Left     = self.ui.label_Tuple__Left_IJ__preFrame
            uiLabel_IJ_Right    = self.ui.label_Tuple__Right_IJ__preFrame
            uiNegativeCheckBox_TargetFrame = self.ui.checkBox_Negative_preFrame
            idx_TargetFrame     = nodeSeqBrowser_Selected.GetSelectedItemNumber() - 1   # preFrame
            if idx_TargetFrame < 0: # PreviousFrame Not Available, SetDefault
                self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Left)
                self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Right)
                return
        elif strFrameType == STR_FRAME_TYPE_NEXT:
            uiLabel_IJ_Left     = self.ui.label_Tuple__Left_IJ__nextFrame
            uiLabel_IJ_Right    = self.ui.label_Tuple__Right_IJ__nextFrame
            uiNegativeCheckBox_TargetFrame = self.ui.checkBox_Negative_nextFrame
            idx_TargetFrame     = nodeSeqBrowser_Selected.GetSelectedItemNumber() + 1   # nextFrame
            if idx_TargetFrame >= nodeSeqBrowser_Selected.GetNumberOfItems(): # NextFrame Not Available, SetDefault
                self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Left)
                self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Right)
                return
        else:
            raise ValueError(f'\n\n\t\t SL_Alert! Wrong strFrameType = {strFrameType}\n')

        # 03. Check and Update:     Negative Frame or Not, including the QCheckBox!
        nodeSeq_Landmarks = nodeSeqBrowser_Selected.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_Landmarks))
        nodePointList_TargetFrame = nodeSeq_Landmarks.GetNthDataNode(idx_TargetFrame)
        str_isNegativeFrame_TargetFrame = nodePointList_TargetFrame.GetAttribute(STR_AttriName_NodePointList_isNegativeFrame)

        num_ControlPoints = nodePointList_TargetFrame.GetNumberOfControlPoints()
        if str_isNegativeFrame_TargetFrame == STR_TRUE:
            if num_ControlPoints > 0:   raise ValueError(f'SL_Alert! num_ControlPoints = {num_ControlPoints}')
            print(f'   **Widget.uiUpdate_LandmarkPositionPanel_TargetFrame(), \tFrameType = {strFrameType}, '
                  f'isNegativeFrame = {str_isNegativeFrame_TargetFrame} \t'
                  f'idx_TargetFrame = {idx_TargetFrame}, num_ControlPoints = {num_ControlPoints}'
                  f'\tSeqBrowser.ID() = {nodeSeqBrowser_Selected.GetID()}')
            self.uiSetNegative_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Left)
            self.uiSetNegative_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Right)
            uiNegativeCheckBox_TargetFrame.checked = True
            return
        elif str_isNegativeFrame_TargetFrame == STR_FALSE:
            uiNegativeCheckBox_TargetFrame.checked = False
        else:   raise ValueError(f'SL_Alert! str_isNegativeFrame_TargetFrame = {str_isNegativeFrame_TargetFrame}')

        # 04. Check if there are ControlPoints to update
        print(f'   **Widget.uiUpdate_LandmarkPositionPanel_TargetFrame(), \tFrameType = {strFrameType}, '
              f'isNegativeFrame = {str_isNegativeFrame_TargetFrame} \t'
              f'idx_TargetFrame = {idx_TargetFrame}, num_ControlPoints = {num_ControlPoints}'
              f'\tSeqBrowser.ID() = {nodeSeqBrowser_Selected.GetID()}')
        if num_ControlPoints <= 0:
            self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Left)
            self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiLabel_IJ_Right)
            return

        # 05. Get Matrix Ready:       mat4x4_World_2_SonixTablet_TargetFrame    &   mat_RASToIJK_TargetFrame
        mat4x4_World_2_SonixTablet_TargetFrame, mat_RASToIJK_TargetFrame, tupleImShape_TargetFrame = \
            self.logic.obtainTargetFrameMatrixes_ForLandmarkPosition(nodeSeqBrowser_Selected, idx_TargetFrame)

        # 06-1. Update uiQLabels of LandmarkPositions for Labeled Landmarks in LIST_LANDMARK_TYPE
        dict_LandmarksToUpdate = getDict_LandmarkLabelsToUpdate()
        for idx_ControlPoint in range(num_ControlPoints):
            uiTargetLabel, str_TargetLandmarkPrefix = self.obtain_uiTargetLabel_from_WholeLabel(nodePointList_TargetFrame, idx_ControlPoint, uiLabel_IJ_Left, uiLabel_IJ_Right)
            dict_LandmarksToUpdate[str_TargetLandmarkPrefix] = False
            self.uiUpdate_LandmarkPositionLabel_OneControlPoint(nodePointList_TargetFrame, idx_ControlPoint, tupleImShape_TargetFrame,
                    mat4x4_World_2_SonixTablet_TargetFrame, mat_RASToIJK_TargetFrame, uiTargetLabel)
        # 06-2. SetDault uiQLabels of LandmarkPositions for Not-Labeled Landmarks in LIST_LANDMARK_TYPE
        for key_LandmarkPrefix in dict_LandmarksToUpdate.keys():
            if dict_LandmarksToUpdate[key_LandmarkPrefix]:
                uiTargetLabel = self.obtain_uiTargetLabel_from_LabelPrefix(key_LandmarkPrefix, uiLabel_IJ_Left, uiLabel_IJ_Right)
                self.uiSetDefault_LandmarkPosition_OneLabelOnly(uiTargetLabel)

    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(self, node_NewActiveBrowser):
        ''' **Widget.uiUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(self, nodeTarget_SeqBrowser) ''' ''''''
        # 00-A. Check if the module isEntered
        if not self.parent.isEntered:       return
        # 00-B. Check the validity of nodeTarget_SeqBrowser
        if not node_NewActiveBrowser:       return

        # 01. Update slider_SeqFrame
        if node_NewActiveBrowser:
            str_CurSeqBrowser_ID = 'node_NewActiveBrowser.GetID() = ' + node_NewActiveBrowser.GetID()
            str_NumberOfItems = 'idx_SeqBrowserSelectedItem = ' + str(node_NewActiveBrowser.GetNumberOfItems())
        else:
            str_CurSeqBrowser_ID = 'node_NewActiveBrowser.GetID() = ' + str(type(node_NewActiveBrowser))
            str_NumberOfItems = ''
        print(f"\t**Widget.uiUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(),  {str_CurSeqBrowser_ID}, {str_NumberOfItems}")
        self.uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(node_NewActiveBrowser)

        # 02. Update Status of  landmarkCollapsibleButton
        self.uiUpdate_CollapsibleButton_LaminaeLandmarks(node_NewActiveBrowser)

    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(self):
        '''         **Widget.uiUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(self) 
            There are two modes to trigger this uiUpdate:   UI modified     /   Non-UI  (node)  modified.
            To guarantee the Non-UI mode, we will update all UI widgets (including the possible TriggerMan UI widget).
            All uiUpdate can be done by logicUpdated nodeSeqBrowser_Selected, thus argument idx_TargetFrame NotRequired.
        ''' ''''''
        # 00-A. Check if the module isEntered
        if not self.parent.isEntered:       return
        # 00-B. Check the validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected:     return

        # 01. Update the uiSlider
        self.uiUpdate_Slider_SeqFrame__by__nodeSeqBrowser_Selected(nodeSeqBrowser_Selected)
        # 02. Update LandmarkPositionLabels
        self.uiUpdate_All_LandmarkPositionPanels_inCollapsibleButton()

    # ------------------------------------------------------------------------------------------------------------------
    def ui_HasLandmarks_uiCollapsibleButtonUpdateNeeded(self, nodeSeqBrowser) -> bool:
        # 01. For case hasLandmarks
        if self.logic.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser):
            return True
        # 02. No nodeSeqBrowser_Selected, or No proxyNode_Landmark found in nodeSeqBrowser_Selected:    SetDefault
        self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton()  # II. In-Brace: uiUpdate
        return False

    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_PushSlicerScreenUpdate_by_ShakeTargetSeqBrowser(self, nodeTarget_SeqBrowser):
        print(f'  **Widget.uiUpdate_PushSlicerScreenUpdate_by_ShakeTargetSeqBrowser()')
        if nodeTarget_SeqBrowser:
            # Let's push Slicer to update by Setting current selected frame back and forth
            idx_curFrame = nodeTarget_SeqBrowser.GetSelectedItemNumber()
            self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton()# To avoid Mismatched idx_curFrame with ui
            nodeTarget_SeqBrowser.SetSelectedItemNumber(max(idx_curFrame - 1, 0))
            self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton()# To avoid Mismatched idx_curFrame with ui
            nodeTarget_SeqBrowser.SetSelectedItemNumber(min(idx_curFrame + 1, nodeTarget_SeqBrowser.GetNumberOfItems() - 1))
            self.uiSetDefault_All_LandmarkPositionPanels_inCollapsibleButton() # To avoid Mismatched idx_curFrame with ui
            nodeTarget_SeqBrowser.SetSelectedItemNumber(idx_curFrame)

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section IV:  updateParameterNodeFromGUI__       ==============================
    # ------------------------------------------------------------------------------------------------------------------
    def updateParameterNodeFromGUI__Set_RefRoleNodeID(self, STR_RefRole, str_NodeID):
        """   Read GUI Method:   Method updateParameterNodeFromGUI__ is called when users makes any change in the GUI.
              Changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
                    **Widget.updateParameterNodeFromGUI__Set_RefRoleNodeID(self, STR_RefRole, str_NodeID）    """''''''
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # I. Before  updating the SingleTon ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        # II.   Update the SingleTon ParameterNode; No updateGUIFromParameterNode triggered in this step
        node_BeforeChange = self._parameterNode.GetNodeReference(STR_RefRole)
        if node_BeforeChange:       str_NodeBeforeChange = self._parameterNode.GetNodeReference(STR_RefRole).GetID()
        else:                       str_NodeBeforeChange = "<class 'NoneType'>"
        print(f'\tBefore Update:  {str_NodeBeforeChange}')
        self._parameterNode.SetNodeReferenceID(STR_RefRole, str_NodeID)
        print(f'\tAfter Update:  {self._parameterNode.GetNodeReference(STR_RefRole).GetID()}')

        # III. After   updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        self._parameterNode.EndModify(wasModified)

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section V:   User-Only UI-Responds          ================================
    # ------------------------------------------------------------------------------------------------------------------
    def onCheckBox_Negative_curFrame_Clicked(self):
        # 00-A. Will do uiUpdate in this function, thus check the billboard self._updatingGUIFromParameterNode
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        print(f'\n\nBeginning of **Widget.onCheckBox_Negative_curFrame_Clicked(self):')
        # 00-B. Check the validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected or nodeSeqBrowser_Selected.GetNumberOfItems() == 0:
            raise ValueError(f'SL_Alert! Every time you get here you must have a valid nodeSeqBrowser_Selected!')

        # I. Before  updating the SingleTon ParameterNode; add this whenever NodeChange, e.g., SetNodeReferenceID()
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
        #---------------------------------------------------------------------------------------------------------------
        #   II-01. Safely get nodeSafeSeq_Landmarks and Set SaveChanges to Positive: may lead to ui_Change by Slicer
        proxyNode_Landmarks = self.getSafe_ProxyLandmarks_TargetSeqBrowser__paramNodeUpdate(nodeSeqBrowser_Selected)
        nodeSafeSeq_Landmarks = nodeSeqBrowser_Selected.GetSequenceNode(proxyNode_Landmarks)
        nodeSeqBrowser_Selected.SetSaveChanges(nodeSafeSeq_Landmarks, True)
        # ---------------------------------------------------------------------------------------------------------------
        # III. After   updating the SingleTon ParameterNode; add this whenever NodeChange, e.g., SetNodeReferenceID()
        self._parameterNode.EndModify(wasModified)

        # 02. Save CheckBox value to Attribute
        #       02-A.   Save Attribute for proxyNode_Landmarks
        str_isNegativeFrame_curFrame = STR_TRUE if self.ui.checkBox_Negative_curFrame.checked else STR_FALSE
        proxyNode_Landmarks.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, str_isNegativeFrame_curFrame)
        #       02-B.   Save Attribute for Sequential_nodePointList
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        nodePointList_Sequential_curFrame = self.logic.obtainDataNode_CurSelected(nodeSeqBrowser_Selected, proxyNode_Landmarks)
        nodePointList_Sequential_curFrame.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, str_isNegativeFrame_curFrame)
        print(f'\n\t**Widget.onCheckBox_Negative_curFrame_Clicked(self),  \t'
              f'ui.checkBox_Negative_curFrame.checked = {self.ui.checkBox_Negative_curFrame.checked}\t'
              f'str_isNegativeFrame_curFrame = {str_isNegativeFrame_curFrame}\n')

        # 03. If isNegativeFrame, we need to Remove all existing ControlPoints; no alert window pop-up to save time
        if self.ui.checkBox_Negative_curFrame.checked:
            # 03-A. Remove from proxyNode_Landmarks:
            proxyNode_Landmarks.RemoveAllControlPoints()
            # 03-B. Remove from Sequential_nodePointList: same procedure, just in case SaveChanges NOT in time!
            nodePointList_Sequential_curFrame.RemoveAllControlPoints()
            # 03-C. Unset TargetFrameLandmark for Landmark_Curves:    Unset + UpdateVisibility
            idx_CurFrame = nodeSeqBrowser_Selected.GetSelectedItemNumber()
            self.logic.updateCurves_UnsetTargetFrameLandmark(nodeSeqBrowser_Selected, idx_CurFrame)
            print(f'\t\t\tRemoveAllControlPoints()')

        # 04. uiUpdate for LandmarkPositionLabels_curFrame (set -1 for both Left/Right labels)
        print(f'\tI. End of CheckBox_Clicked, now we Update curFrame \t STR_FRAME_TYPE_CURRENT')
        self._updatingGUIFromParameterNode = True  # I. Open-Brace:  Avoid updateParameterNodeFromGUI__ (infinite loop)
        self.uiUpdate_LandmarkPositionPanel_TargetFrame(strFrameType=STR_FRAME_TYPE_CURRENT) # II. In-Brace: uiUpdate
        self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;

    # ------------------------------------------------------------------------------------------------------------------
    def onPushButton_DropLeft_Clicked(self):
        print("**Widget.onPushButton_DropLeft_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        # 01. Setup str_TargetLandmarkType
        self.logic.setUserLandmarkLabeling_strLandmarkType(STR_LandmarkType_LeftLamina)
        # 02. Active the annotation:    StartPlaceMode for node_SeqBrowserProxy_Landmarks
        self.startPlaceControlPoint_SeqBrowserProxy_Landmarks(bool_Persistent=False)

    def onPushButton_StartSeqLabeling_Clicked(self):
        print("**Widget.onPushButton_StartSeqLabeling_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        # 01. Need to set up again based on the proxy node
        self.logic.setUserLandmarkLabeling_strLandmarkType(STR_LabelButton_Sequential)
        # 02. Active the annotation:    StartPlaceMode for node_SeqBrowserProxy_Landmarks
        self.startPlaceControlPoint_SeqBrowserProxy_Landmarks(bool_Persistent=True)

    def onPushButton_DropRight_Clicked(self):
        print("**Widget.onPushButton_DropRight_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        # 01. Setup str_TargetLandmarkType
        self.logic.setUserLandmarkLabeling_strLandmarkType(STR_LandmarkType_RightLamina)
        # 02. Active the annotation:    StartPlaceMode for node_SeqBrowserProxy_Landmarks
        self.startPlaceControlPoint_SeqBrowserProxy_Landmarks(bool_Persistent=False)

    # ------------------------------------------------------------------------------------------------------------------
    def onPushButton_DeleteLeft_Clicked(self):
        print("**Widget.onPushButton_DeleteLeft_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        pass

    def onPushButton_DeleteFrameLandmark_Clicked(self):
        print("**Widget.onPushButton_DeleteFrameLandmark_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        pass

    def onPushButton_DeleteRight_Clicked(self):
        print("**Widget.onPushButton_DeleteRight_Clicked(self), \tSL_Developer, F-Slot"); test = 0; test += 1
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def startPlaceControlPoint_SeqBrowserProxy_Landmarks(self, bool_Persistent = False):
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if nodeSeqBrowser_Selected:
            # I. Before  updating the SingleTon ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
            wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
            # --------------------------------------------------------------------------------------------------------------
            # II. Update the SingleTon ParameterNode; No updateGUIFromParameterNode triggered in this step
            #       II-01. Get :                node_SeqBrowserProxy_Landmarks,  the PointList_ProxyNode for Landmarks
            node_SeqBrowserProxy_Landmarks = self.getSafe_ProxyLandmarks_TargetSeqBrowser__paramNodeUpdate(nodeSeqBrowser_Selected)
            #       II-02. Set CurrentActive:   node_SeqBrowserProxy_Landmarks,  the PointList_ProxyNode for Landmarks
            slicer.modules.markups.logic().SetActiveList(node_SeqBrowserProxy_Landmarks)
            #       II-03. Trigger the MarkUp ControlPoint-Drop function, so users
            #                   can manually drop a ControlPoint and add to CurrentActive (curFrame) MarkUp-PointList
            slicer.modules.markups.logic().StartPlaceMode(bool_Persistent)
            # --------------------------------------------------------------------------------------------------------------
            # III. After   updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
            self._parameterNode.EndModify(wasModified)
        else:
            raise ValueError(f'\n\t\t\tSL_Alert!! nodeSeqBrowser_Selected not found !!\n')

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def qMessageBox_Critical_RaiseValueError(self, str_Message):
        self.qMessageBox_Critical(str_Message)
        raise ValueError(str_Message)
    # ------------------------------------------------------------------------------------------------------------------
    def qMessageBox_Critical(self, str_Message):
        msg = QMessageBox();                msg.setWindowTitle(self.logic.moduleName)
        msg.setText(str_Message);           msg.setIcon(QMessageBox.Critical)
        msg.exec_()

    def qMessageBox_Information(self, str_Message):
        msg = QMessageBox();                msg.setWindowTitle(self.logic.moduleName)
        msg.setText(str_Message);           msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def qMessageBox_Question(self, str_Message):
        msg = QMessageBox();                msg.setWindowTitle(self.logic.moduleName)
        msg.setText(str_Message);           msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        int_QResult = msg.exec_()
        return int_QResult

    # ------------------------------------------------------------------------------------------------------------------
    def onPushButton_Output_SeqNumpyLandmarks_Clicked(self):
        print("**Widget.onPushButton_Output_SeqNumpyLandmarks_Clicked(self), \tSL_Developer")
        # 00. No landmarks to generate if the SeqBrowser_Selected does not contain the sequence of Landmarks
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if self.logic.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser_Selected) == False:
            self.qMessageBox_Critical("No Landmark to Output!")
            return

        # 01. Get strFileName_NumpyLandmark
        strFileName_NumpyLandmark = self.logic.obtainStr_FileName_NumpyLandmark(nodeSeqBrowser_Selected.GetName())
        # 02. Get strFilePath_NumpyLandmark
        strFilePath_NumpyLandmark = f'{self.logic.obtainStr_SceneFileFolder(nodeSeqBrowser_Selected)}/{strFileName_NumpyLandmark}'
        # 03. Get Numpy Array
        arr_NumpyLandmarks_OneSequence = self.logic.obtainArr_NumpyLandmark_OneSequence(nodeSeqBrowser_Selected)
        # 04. Save NumpyArray to disk
        np.save(strFilePath_NumpyLandmark, arr_NumpyLandmarks_OneSequence)
        # 05. Pop-up success window
        self.qMessageBox_Information(f"Output Successfully! \n\nFile saved at: \n\n{strFilePath_NumpyLandmark}")

    # ------------------------------------------------------------------------------------------------------------------
    def onPushButton_Load_SeqNumpyLandmarks_Clicked(self):
        print("**Widget.onPushButton_Load_SeqNumpyLandmarks_Clicked(self), \tSL_Developer")
        # 01. Check if there are existing landmarks in the current active SeqBrowser
        nodeSeqBrowser_Selected = self._parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        is_HadLandmarksBeforeFileLoad = self.logic.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser_Selected)
        if is_HadLandmarksBeforeFileLoad:
            int_QResult = self.qMessageBox_Question("Load a NumpyLandmark file will\n\treplace all existing landmarks!"
                                      "\n\nAre you sure you want to continue?")
            if int_QResult == QMessageBox.Cancel:
                return

        # 02. Pop out OpenFile-Dialog to let users choose the NumpyLandmark file
        strFilePath_NumpyLandmarks, _ = QFileDialog.getOpenFileName(caption='Load target NumpyLandmark file', \
                                    directory=slicer.mrmlScene.GetRootDirectory(), filter="NumpyLandmark file (*.npy)")
        if not strFilePath_NumpyLandmarks:
            return

        # 03. Check file shape of the loaded numpy file
        arr_SeqNumpyLandmarks = np.load(strFilePath_NumpyLandmarks)
        num_TotalFrames = nodeSeqBrowser_Selected.GetNumberOfItems()
        if arr_SeqNumpyLandmarks.shape != (num_TotalFrames, len(LIST_LANDMARK_TYPE), len(LIST_NumpyLandmark_VarType)):
            self.qMessageBox_Critical(f'File not matched! \n\n'
                    f'Expect\t  file shape = ({num_TotalFrames}, {len(LIST_LANDMARK_TYPE)}, {len(LIST_NumpyLandmark_VarType)})'
                    f'\n\nBut selected file shape = {arr_SeqNumpyLandmarks.shape} !!')
            return

        # 04. Safely Update proxyNode_Landmarks:    if not landmark before, safely Initialize proxyNode_Landmarks
        #   04-I. Before  updating the SingleTon ParameterNode; add this whenever NodeChange, e.g., SetNodeReferenceID()
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
        # ---------------------------------------------------------------------------------------------------------------
        #   04-II-01. Safely get nodeSafeSeq_Landmarks and Set SaveChanges to Positive: may lead to ui_Change by Slicer
        proxyNode_Landmarks = self.getSafe_ProxyLandmarks_TargetSeqBrowser__paramNodeUpdate(nodeSeqBrowser_Selected)
        #               Upate    proxyNode_Landmarks    but     NOT updateCurves
        idx_CurSelectedFrame = nodeSeqBrowser_Selected.GetSelectedItemNumber()
        arr_ProxyFrameLandmarks_RAS = arr_SeqNumpyLandmarks[idx_CurSelectedFrame][:, LIST_NumpyLandmark_VarType.index(STR_NumpyLandmark_Var_R):]
        self.updateFrameLandmarks_given_NumpyArray__uiAssert(nodeSeqBrowser_Selected, idx_CurSelectedFrame,  \
                                                proxyNode_Landmarks, arr_ProxyFrameLandmarks_RAS, isUpdateCurves=False)
        #               Get     nodeSafeSeq_Landmarks   &   SetSaveChanges
        nodeSafeSeq_Landmarks = nodeSeqBrowser_Selected.GetSequenceNode(proxyNode_Landmarks)
        nodeSeqBrowser_Selected.SetSaveChanges(nodeSafeSeq_Landmarks, True)
        # ---------------------------------------------------------------------------------------------------------------
        #   04-III. After updating the SingleTon ParameterNode; add this whenever NodeChange, e.g., SetNodeReferenceID()
        self._parameterNode.EndModify(wasModified)

        # 05. Load Landmarks frame-by-frame
        for idx_Frame in range(num_TotalFrames):
            arr_FrameLandmarks_RAS = arr_SeqNumpyLandmarks[idx_Frame][:, LIST_NumpyLandmark_VarType.index(STR_NumpyLandmark_Var_R) :]
            node_SeqPointList = nodeSafeSeq_Landmarks.GetNthDataNode(idx_Frame)

            self.updateFrameLandmarks_given_NumpyArray__uiAssert(nodeSeqBrowser_Selected, idx_Frame, node_SeqPointList,\
                                                            arr_FrameLandmarks_RAS, isUpdateCurves=True)
        # 06. uiUpdate:     landmarkCollapsibleButton
        if self.parent.isEntered:
            self._updatingGUIFromParameterNode = True   # I. Open-Brace
            self.uiUpdate_All_LandmarkPositionPanels_inCollapsibleButton() # II. uiUpdate:     landmarkCollapsibleButton
            self._updatingGUIFromParameterNode = False  # III. Close-Brace: All the GUI updates are done;

    # ------------------------------------------------------------------------------------------------------------------
    def updateFrameLandmarks_given_NumpyArray__uiAssert(self, node_SeqBrowser, idx_TargetFrame, node_PointList, \
                                                                arr_FrameLandmarks_RAS, isUpdateCurves = True):
        """  **Widget.updateFrameLandmarks_given_NumpyArray__uiAssert() 
                    node_PointList can either be proxyNode_Landmarks or nodePointList_Sequential   """''''''
        # 00. Check shape of arr_FrameLandmarks_RAS
        if arr_FrameLandmarks_RAS.shape != (len(LIST_LANDMARK_TYPE), NumVar_NumpyLandmark_RAS):
            self.qMessageBox_Critical_RaiseValueError(f'arr_FrameLandmarks_RAS.shape = {arr_FrameLandmarks_RAS.shape}!')

        # 01. Initialize
        #       01-A. Remove all ControlPoints from node_PointList
        node_PointList.RemoveAllControlPoints()
        #       01-B. If not isUpdateCurves, Unset TargetFrameLandmark for Landmark_Curves:    Unset + UpdateVisibility
        if isUpdateCurves:
            self.logic.updateCurves_UnsetTargetFrameLandmark(node_SeqBrowser, idx_TargetFrame)

        # 02. Check if Negative;    Set Attribute for     is_NegativeFrame
        if arr_FrameLandmarks_RAS[0, 0] == INT_NEGATIVE_RAS_VALUE:
            if arr_FrameLandmarks_RAS.sum() != INT_NEGATIVE_RAS_VALUE * arr_FrameLandmarks_RAS.size:
                self.qMessageBox_Critical_RaiseValueError(f'arr_FrameLandmarks_RAS = \n{arr_FrameLandmarks_RAS}!')
            # Return if negative frame
            node_PointList.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, STR_TRUE)   #   Negative
            return
        else:
            node_PointList.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, STR_FALSE)  #   Default / Defined

        # 03. If not Negative frame, update landmark_RAS one ControlPoint by one ControlPoint
        for idx_LandmarkType in range(len(LIST_LANDMARK_PREFIX)):
            str_LandmarkPrefix      = LIST_LANDMARK_PREFIX[idx_LandmarkType]
            vec_RAS_WorldPosition   = arr_FrameLandmarks_RAS[idx_LandmarkType]
            # 03-A. For case    Default / (Landmark Not Available),     continue
            if vec_RAS_WorldPosition[0] == INT_DEFAULT_RAS_VALUE:
                if vec_RAS_WorldPosition.sum() != INT_DEFAULT_RAS_VALUE * vec_RAS_WorldPosition.size:
                    self.qMessageBox_Critical_RaiseValueError(f'vec_RAS_WorldPosition = \n{vec_RAS_WorldPosition}!')
                continue
            # 03-B. For case PositionDefined
            #       03-B-i. Update node_PointList
            if str_LandmarkPrefix == STR_ControlPointLabelPrefix_Left:
                str_LandmarkLabel = self.logic.obtainStr_LandmarkLabel_LeftLamina(node_SeqBrowser.GetName(), idx_TargetFrame + INT_SliderFrameIndex_Min)
            elif str_LandmarkPrefix == STR_ControlPointLabelPrefix_Right:
                str_LandmarkLabel = self.logic.obtainStr_LandmarkLabel_RightLamina(node_SeqBrowser.GetName(), idx_TargetFrame + INT_SliderFrameIndex_Min)
            node_PointList.AddControlPointWorld(vec_RAS_WorldPosition, str_LandmarkLabel)
            if node_PointList.GetNumberOfDefinedControlPoints() > len(LIST_LANDMARK_PREFIX):
                self.qMessageBox_Critical_RaiseValueError(f'num_DefinedControlPoints = {node_PointList.GetNumberOfDefinedControlPoints()}')
            #       03-B-ii. Update Curves
            if isUpdateCurves:
                self.logic.updateCurves_OneLandmark_TargetFrame_GivenRAS(node_SeqBrowser, idx_TargetFrame, str_LandmarkPrefix, vec_RAS_WorldPosition)


    # ------------------------------------------------------------------------------------------------------------------
''' ================================================================================================================='''
#
# sl_01__LaminaLandmark_LabelingLogic
#
class sl_01__LaminaLandmark_LabelingLogic(ScriptedLoadableModuleLogic):
    """   The Logic class is :  to facilitate dynamic reloading of the module without restarting the application.
          This class should implement all the actual computation done by your module.  
          The interface should be such that other python code can import this class 
                                        and make use of the functionality without requiring an instance of the Widget.
        Uses ScriptedLoadableModuleLogic base class, available at:
            https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """''''''

    def __init__(self):
        """    Called when the logic class is instantiated. Can be used for initializing member variables.    """
        ScriptedLoadableModuleLogic.__init__(self)

        self.str_TargetLandmarkType = LIST_LANDMARK_TYPE[0] # Initial the first LandmarkType
        self._isSwitchingSeqBrowser = False

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section VI:  get, set, obtain, & createNewNode          =====================
    # ------------------------------------------------------------------------------------------------------------------
    def get_isSwitchingSeqBrowser(self):                     return self._isSwitchingSeqBrowser
    def set_isSwitchingSeqBrowser(self, isSwitchingSeqBrowser):     self._isSwitchingSeqBrowser = isSwitchingSeqBrowser
    # ------------------------------------------------------------------------------------------------------------------
    def getUserLandmarkLabeling_strLandmarkType(self):                  return  self.str_TargetLandmarkType
    def setUserLandmarkLabeling_strLandmarkType(self, STR_TargetLandmarkType):  self.str_TargetLandmarkType = STR_TargetLandmarkType
    # ------------------------------------------------------------------------------------------------------------------
    def obtainIndex_SeqBrowserNameIndex_ForLabelName(self, str_SeqBroswerName):
        listInfo_SeqBroswer = str_SeqBroswerName.split('__')
        if 'SeqBrowser' in listInfo_SeqBroswer[0].split('_'):   return      listInfo_SeqBroswer[0].split('_')[1]
        else:                                                   return      None

    def obtain__LablePrefix_IdxFrame__from_ControlPointLabel(self, strLabel_ControlPoint):
        strInfo_NonSeqBrowser = strLabel_ControlPoint.split('_')[-1]    # refer to obtainStr_LandmarkLabel_LeftLamina
        if STR_ControlPointLabelPrefix_Left in strInfo_NonSeqBrowser:
            str_LabelPrefix = STR_ControlPointLabelPrefix_Left;         idx_SlicerFrame = int(strInfo_NonSeqBrowser[1:])
        elif STR_ControlPointLabelPrefix_Right in strInfo_NonSeqBrowser:
            str_LabelPrefix = STR_ControlPointLabelPrefix_Right;        idx_SlicerFrame = int(strInfo_NonSeqBrowser[1:])
        elif STR_ControlPointLabelShort_SpinalCord in strInfo_NonSeqBrowser:
            str_LabelPrefix = STR_ControlPointLabelShort_SpinalCord;    idx_SlicerFrame = int(strInfo_NonSeqBrowser[2:])
        else:
            raise ValueError(f'SL_Alert! strLabel_ControlPoint = {strLabel_ControlPoint}')
        idxFrame = idx_SlicerFrame - INT_SliderFrameIndex_Min
        return str_LabelPrefix, idxFrame

    def obtainStr_LandmarkLabel_LeftLamina(self, str_SeqBroswerName, idx_SliderFrame):
        idx_SeqBrowserName = self.obtainIndex_SeqBrowserNameIndex_ForLabelName(str_SeqBroswerName)
        if idx_SeqBrowserName:      return  f's{idx_SeqBrowserName}_{STR_ControlPointLabelPrefix_Left}{idx_SliderFrame}'
        else:                       return  f'{STR_ControlPointLabelPrefix_Left}{idx_SliderFrame}'

    def obtainStr_LandmarkLabel_RightLamina(self, str_SeqBroswerName, idx_SliderFrame):
        idx_SeqBrowserName = self.obtainIndex_SeqBrowserNameIndex_ForLabelName(str_SeqBroswerName)
        if idx_SeqBrowserName:      return  f's{idx_SeqBrowserName}_{STR_ControlPointLabelPrefix_Right}{idx_SliderFrame}'
        else:                       return  f'{STR_ControlPointLabelPrefix_Right}{idx_SliderFrame}'

    def obtainStr_CurveControlPointLabel_SpinalCord(self, str_SeqBroswerName, idx_SliderFrame):
        idx_SeqBrowserName = self.obtainIndex_SeqBrowserNameIndex_ForLabelName(str_SeqBroswerName)
        if idx_SeqBrowserName:  return  f's{idx_SeqBrowserName}_{STR_ControlPointLabelShort_SpinalCord}{idx_SliderFrame}'
        else:                   return  f'{STR_ControlPointLabelShort_SpinalCord}{idx_SliderFrame}'

    def obtainStrNodeName_Sequence_pList_Landmarks(self, str_SeqBroswerName):  
        listInfo_SeqBroswer = str_SeqBroswerName.split('__')
        if 'SeqBrowser' in listInfo_SeqBroswer[0].split('_'):
            idx_SeqBrowser = listInfo_SeqBroswer[0].split('_')[1]
            strNodeName_SequenceLandmarks = f'Landmarks_{idx_SeqBrowser}__{listInfo_SeqBroswer[1]}__{listInfo_SeqBroswer[2]}'
        else:
            strNodeName_SequenceLandmarks = f'Landmarks'
        return strNodeName_SequenceLandmarks

    def obtainStrNodeName_LandmarkCurve(self, str_SeqBroswerName, str_CurveType):
        if   str_CurveType == STR_LandmarkType_LeftLamina:  str_CurveTypeCapitcal = STR_ControlPointLabelPrefix_Left
        elif str_CurveType == STR_LandmarkType_RightLamina: str_CurveTypeCapitcal = STR_ControlPointLabelPrefix_Right
        elif str_CurveType == STR_LandmarkCurveType_SpinalCord: str_CurveTypeCapitcal = STR_ControlPointLabelShort_SpinalCord
        else:   raise ValueError(f'SL_Alert! str_CurveType = {str_CurveType}')

        idx_SeqBrowserName = self.obtainIndex_SeqBrowserNameIndex_ForLabelName(str_SeqBroswerName)
        if idx_SeqBrowserName:      return  f'c{idx_SeqBrowserName}_{str_CurveTypeCapitcal}'
        else:                       return  f'{str_CurveTypeCapitcal}'

    # ------------------------------------------------------------------------------------------------------------------
    def obtainStr_SceneFileFolder(self, nodeSeqBrowser):
        """     You can construct absolute paths from various directories, for example:
            slicer.mrmlScene.GetRootDirectory(): all nodes are saved relative to this path
            slicer.app.temporaryPath: write-able folder, you can use this to store any temporary data
            slicer.app.slicerHome: Slicer core binary folder
            slicer.app.extensionsInstallPath: Slicer extensions folder
            slicer.modules.sampledata.path: path of a scripted module (in this example: Sample Data module) """''''''
        '''
        # 00-A. No landmarks to generate if the SeqBrowser_Selected does not contain the sequence of Landmarks
        if not nodeSeqBrowser:  raise ValueError(f'SL_Alert! nodeSeqBrowser = {nodeSeqBrowser}'); return
        # 00-B. Check if nodeSeqBrowser_Selected.GetSelectedItemNumber() is Valid
        idx_curFrame = nodeSeqBrowser.GetSelectedItemNumber()
        if idx_curFrame < 0 or idx_curFrame >= nodeSeqBrowser.GetNumberOfItems():
            raise ValueError(f'SL_Alert! Incorrect nodeSeqBrowser_Selected.GetSelectedItemNumber() = {idx_curFrame}')
            return

        # 01. Get  str_SceneFileFolder  based on nodeSeq_2DScan
        nodeSeq_2DScan = nodeSeqBrowser.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_2DScan))
        self.str_SceneFileFolder = os.path.dirname(nodeSeq_2DScan.GetStorageNode().GetFileName())
        return self.str_SceneFileFolder            '''

        return slicer.mrmlScene.GetRootDirectory()


    def obtainStr_FileName_NumpyLandmark(self, str_SeqBroswerName):
        strFileName_NumpyLandmark = f'{self.obtainStrNodeName_Sequence_pList_Landmarks(str_SeqBroswerName)}__Coord2D3D.npy'
        return strFileName_NumpyLandmark

    # ------------------------------------------------------------------------------------------------------------------
    def obtainSafe_idxPreFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser):
        ''' **Logic.obtainSafe_idxPreFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser) ''' ''''''
        idx_preFrame = max(nodeTarget_SeqBrowser.GetSelectedItemNumber() - 1, 0)
        return idx_preFrame
    def obtainSafe_idxNextFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser):
        ''' **Logic.obtainSafe_idxNextFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser) ''' ''''''
        idx_nextFrame = min(nodeTarget_SeqBrowser.GetSelectedItemNumber() + 1, nodeTarget_SeqBrowser.GetNumberOfItems() - 1)
        return idx_nextFrame
    def obtain_idxSliderCurFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser):
        ''' **Logic.obtain_idxSliderCurFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser) ''' ''''''
        idx_SliderCurFrame = nodeTarget_SeqBrowser.GetSelectedItemNumber() + INT_SliderFrameIndex_Min
        return idx_SliderCurFrame

    # ------------------------------------------------------------------------------------------------------------------
    def obtainProxyNode_Landmarks_from_SeqBrowser(self, nodeSeqBrowser):
        ''' **Logic.obtainProxyNode_Landmarks_from_SeqBrowser(self, nodeSeqBrowser), SL_Proxy ''' ''''''
        if not nodeSeqBrowser:
            return None

        # 00. Initial node_ProxyLandmarks
        node_ProxyLandmarks = None

        # 01. Check if there is already a NodeReference saved in nodeSeqBrowser
        numNodeRef_Proxy = nodeSeqBrowser.GetNumberOfNodeReferences(STR_pListNode_RefRole_LandmarkProxy)
        if numNodeRef_Proxy == 1:
            # 01-A. Expected case, pList_LeftLamina exists and there is only one
            node_ProxyLandmarks = nodeSeqBrowser.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            print(f'\t\t\t\t\t Found {node_ProxyLandmarks.GetName()}.GetID() = {node_ProxyLandmarks.GetID()}')

        elif numNodeRef_Proxy > 1:
            print('\n\n\tSL__Allert!! There should not be more than one numNodeRef_Proxy!!\n\n')
            # 01-B. Un-Expected case, we return the first  nodeSeq using the same ReferenceRole
            node_ProxyLandmarks = nodeSeqBrowser.GetNthNodeReference(STR_pListNode_RefRole_LandmarkProxy, 0)
            print(f'\t\tChoose first {node_ProxyLandmarks.GetName()}.GetID() = {node_ProxyLandmarks.GetID()}')

        return node_ProxyLandmarks
    # ------------------------------------------------------------------------------------------------------------------
    def obtainDataNode_CurSelected(self, nodeSeqBrowser_Target, nodeProxy_Target):
        idxFrame_CurSelected = nodeSeqBrowser_Target.GetSelectedItemNumber()
        print(f'\n\t\t\t **Logic.obtainDataNode_CurSelected(): idxFrame_CurSelected = {idxFrame_CurSelected}\n')
        nodeSeq_Target = nodeSeqBrowser_Target.GetSequenceNode(nodeProxy_Target)
        nodeData_CurSelectedFrame_Target = nodeSeq_Target.GetNthDataNode(idxFrame_CurSelected)
        return nodeData_CurSelectedFrame_Target

    # ------------------------------------------------------------------------------------------------------------------
    def obtainTargetFrameMatrixes_ForLandmarkPosition(self, nodeSeqBrowser, idx_TargetFrame):
        ''' **Logic.obtainTargetFrameMatrixes_ForLandmarkPosition(self, nodeSeqBrowser, idx_TargetFrame) ''' ''''''
        # 00. Check the validity of idx_TargetFrame
        if not self.isValid_idxTargetFrame(nodeSeqBrowser, idx_TargetFrame):
            raise ValueError(f'SL_Alert! Invalid idx_TargetFrame = {idx_TargetFrame}')
            return

        # 01. Get   mat4x4_World_2_SonixTablet_TargetFrame
        nodeSeq_LinearTransform = nodeSeqBrowser.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_LinearTransform))
        nodeLinearTransform_TargetFrame = nodeSeq_LinearTransform.GetNthDataNode(idx_TargetFrame)
        mat4x4_SonixTablet_2_World_TargetFrame = vtk.vtkMatrix4x4()
        nodeLinearTransform_TargetFrame.GetMatrixTransformToWorld(mat4x4_SonixTablet_2_World_TargetFrame)
        mat4x4_World_2_SonixTablet_TargetFrame = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4.Invert(mat4x4_SonixTablet_2_World_TargetFrame, mat4x4_World_2_SonixTablet_TargetFrame)
        # 02. Get   node2DScan_TargetFrame -> mat_RASToIJK_TargetFrame:     to guarantee the Code-Scalability
        nodeSeq_2DScan = nodeSeqBrowser.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_2DScan))
        node2DScan_TargetFrame = nodeSeq_2DScan.GetNthDataNode(idx_TargetFrame)
        mat_RASToIJK_TargetFrame = vtk.vtkMatrix4x4()
        node2DScan_TargetFrame.GetRASToIJKMatrix(mat_RASToIJK_TargetFrame)
        # 03. Get   tupleImShape_TargetFrame:   to detect landmark being in-Frame or out-Frame
        vtkImageData_TargetFrame = node2DScan_TargetFrame.GetImageData()
        tupleImShape_TargetFrame = vtkImageData_TargetFrame.GetDimensions()

        return mat4x4_World_2_SonixTablet_TargetFrame, mat_RASToIJK_TargetFrame, tupleImShape_TargetFrame

    # ------------------------------------------------------------------------------------------------------------------
    def obtain__IJK_SonixTablet__from__RAS_World(self, vtkVec3d_RAS_World, mat4x4_World_2_SonixTablet, mat_RASToIJK):
        # 01. Apply LinearTransform_curFrame to vtkVec3d_RAS_World Coordinates, to get tuple4D_RAS_SonixTablet
        tuple4D_RAS_SonixTablet = mat4x4_World_2_SonixTablet.MultiplyPoint(list(vtkVec3d_RAS_World) + [1.0])
        # 02. Get and Apply RASToIJKMatrix to tuple4D_RAS_SonixTablet, to get tuple4D_IJK_SonixTablet
        tuple4D_IJK_SonixTablet = mat_RASToIJK.MultiplyPoint(tuple4D_RAS_SonixTablet)

        return tuple4D_IJK_SonixTablet

    # ------------------------------------------------------------------------------------------------------------------
    def hasLandmarks_inTargetNode_SeqBrowser(self, nodeSeqBrowser) -> bool:
        if nodeSeqBrowser:
            proxyNode_Landmark = nodeSeqBrowser.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            if proxyNode_Landmark:
                nodeSeq_Landmarks = nodeSeqBrowser.GetSequenceNode(proxyNode_Landmark)
                if nodeSeq_Landmarks and nodeSeqBrowser.GetNumberOfItems() == nodeSeq_Landmarks.GetNumberOfDataNodes():
                    return True
                else:
                    if nodeSeq_Landmarks:
                        print(f'\n\tnodeSeq_Landmarks.Number_DataNodes = {nodeSeq_Landmarks.GetNumberOfDataNodes()}\n')
                    else:   print(f'type(nodeSeq_Landmarks) = {type(nodeSeq_Landmarks)}')
        return False

    # ------------------------------------------------------------------------------------------------------------------
    def obtainArr_NumpyLandmark_OneFrame(self, nodeSeqBrowser, idx_TargetFrame, node_PointList):
        """ **Logic.obtainArr_NumpyLandmark_OneFrame(self, nodeSeqBrowser, idx_TargetFrame) """''''''
        # 00. Initialize arr_FrameLandmarks
        arr_FrameLandmarks = INT_DEFAULT_RAS_VALUE * \
                                    np.ones([len(LIST_LANDMARK_TYPE), len(LIST_NumpyLandmark_VarType)], dtype=float)
        # 01. No landmarks to generate if the SeqBrowser_Selected does not contain the sequence of Landmarks
        if self.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser) == False:
            raise ValueError('SL_Alert! Should not be called if no landmarks');
            return arr_FrameLandmarks

        # 02. Return if isNegativeFrame
        str_isNegativeFrame = node_PointList.GetAttribute(STR_AttriName_NodePointList_isNegativeFrame)
        if str_isNegativeFrame == STR_TRUE:
            if node_PointList.GetNumberOfDefinedControlPoints() > 0:
                raise ValueError(f'num_DefinedControlPoints = {node_PointList.GetNumberOfDefinedControlPoints()}')
            # Set FrameLandmark value:  INT_NEGATIVE_RAS_VALUE
            arr_FrameLandmarks = INT_NEGATIVE_RAS_VALUE * \
                                 np.ones([len(LIST_LANDMARK_TYPE), len(LIST_NumpyLandmark_VarType)], dtype=float)
            return arr_FrameLandmarks
        elif str_isNegativeFrame == STR_FALSE:  pass
        else:
            raise ValueError(f'SL_Alert! str_isNegativeFrame_TargetFrame = {str_isNegativeFrame}')
            return arr_FrameLandmarks

        # 03. Return if no available ControlPoints to update
        num_DefinedControlPoints = node_PointList.GetNumberOfDefinedControlPoints()
        if num_DefinedControlPoints <= 0:       return arr_FrameLandmarks

        # 04-1. Get Matrix Ready:       mat4x4_World_2_SonixTablet_TargetFrame    &   mat_RASToIJK_TargetFrame
        mat4x4_World_2_SonixTablet, mat_RASToIJK, tupleImShape_TargetFrame = \
            self.obtainTargetFrameMatrixes_ForLandmarkPosition(nodeSeqBrowser, idx_TargetFrame)

        # 04-2. Get LandmarkPositions for Labeled Landmarks in LIST_LANDMARK_TYPE
        dict_LandmarksToUpdate = getDict_LandmarkLabelsToUpdate()
        for idx_ControlPoint in range(node_PointList.GetNumberOfControlPoints()):
            # 04-2-A. Check if the ControlPoint is Defined; continue if not
            if node_PointList.GetNthControlPointPositionStatus(idx_ControlPoint) \
                                                    != slicer.vtkMRMLMarkupsNode.PositionDefined:       continue
            # 04-2-B. Get Coord2D3D:    tuple4D_IJK_SonixTablet   +   vtkVec3d_RAS_World
            #       04-2-B-a. Get   RAS_ControlPoint:     vtkVec3d_RAS_World Coordinates
            vtkVec3d_RAS_World = node_PointList.GetNthControlPointPositionVector(idx_ControlPoint)
            #       04-2-B-b. Get tuple4D_IJK_SonixTablet;    SL_Note: image IJK_Coords stay in SonixTablet_Coordinates
            tuple4D_IJK_SonixTablet = self.obtain__IJK_SonixTablet__from__RAS_World(    \
                                                        vtkVec3d_RAS_World, mat4x4_World_2_SonixTablet, mat_RASToIJK)
            # 04-2-C. For the PositionDefined ControlPoint, get:     idx_LandmarkType
            str_ControPoint_Label = node_PointList.GetNthControlPointLabel(idx_ControlPoint)
            if STR_ControlPointLabelPrefix_Left in str_ControPoint_Label:
                str_TargetLandmarkPrefix = STR_ControlPointLabelPrefix_Left
                idx_LandmarkType = LIST_LANDMARK_PREFIX.index(STR_ControlPointLabelPrefix_Left)
            elif STR_ControlPointLabelPrefix_Right in str_ControPoint_Label:
                str_TargetLandmarkPrefix = STR_ControlPointLabelPrefix_Right
                idx_LandmarkType = LIST_LANDMARK_PREFIX.index(STR_ControlPointLabelPrefix_Right)
            else:
                raise ValueError(f'\n\n\t\t SL_Alert! Wrong label = {str_ControPoint_Label}\n');
                return  arr_FrameLandmarks
            if idx_LandmarkType < 0 or idx_LandmarkType >= len(LIST_LANDMARK_PREFIX):
                raise ValueError(f'SL_Alert! idx_LandmarkType = {idx_LandmarkType}')
                return arr_FrameLandmarks

            # 04-2-D. Fill up   for     idx_LandmarkType:      dict_LandmarksToUpdate      +       arr_FrameLandmarks
            dict_LandmarksToUpdate[str_TargetLandmarkPrefix] = False
            arr_FrameLandmarks[idx_LandmarkType] = \
                        [round(tuple4D_IJK_SonixTablet[0]),round(tuple4D_IJK_SonixTablet[1])] + list(vtkVec3d_RAS_World)

        return arr_FrameLandmarks

    # ------------------------------------------------------------------------------------------------------------------
    def obtainArr_NumpyLandmark_OneSequence(self, nodeSeqBrowser):
        """ **Logic.obtainArr_NumpyLandmark_OneSequence(self, nodeSeqBrowser) """''''''
        # 00. No landmarks to generate if the SeqBrowser_Selected does not contain the sequence of Landmarks
        if self.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser) == False:
            raise ValueError('SL_Alert! Should not be called if no landmarks'); return

        nodeSeq_Landmarks = nodeSeqBrowser.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_Landmarks))
        if nodeSeqBrowser.GetNumberOfItems() != nodeSeq_Landmarks.GetNumberOfDataNodes():
            raise ValueError(f'nodeSeq_Landmarks.GetNumberOfDataNodes() = {nodeSeq_Landmarks.GetNumberOfDataNodes()}')
        num_DataNodes = nodeSeqBrowser.GetNumberOfItems()
        arr_SequenceLandmarks = INT_DEFAULT_RAS_VALUE * \
                    np.ones([num_DataNodes, len(LIST_LANDMARK_TYPE), len(LIST_NumpyLandmark_VarType)], dtype = float)
        for idx_DataNode in range(num_DataNodes):
            node_PointList = nodeSeq_Landmarks.GetNthDataNode(idx_DataNode)
            arr_FrameLandmarks = self.obtainArr_NumpyLandmark_OneFrame(nodeSeqBrowser, idx_DataNode, node_PointList)
            arr_SequenceLandmarks[idx_DataNode] = arr_FrameLandmarks

        return arr_SequenceLandmarks

    # ------------------------------------------------------------------------------------------------------------------
    def createNewNode_SequenceLandmarks(self, nodeSeqBrowser, node_SeqBrowserProxy_Landmarks):
        ''' **Logic.createNewNode_SequenceLandmarks(self, nodeSeqBrowser, node_SeqBrowserProxy_Landmarks) ''' ''''''
        # 01. Get NodeName
        strNodeName_Sequence_pList_Landmarks = self.obtainStrNodeName_Sequence_pList_Landmarks(nodeSeqBrowser.GetName())
        # 02. Add NewNode to the mrmlScene
        nodeSeq_Landmarks = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode", strNodeName_Sequence_pList_Landmarks)

        # Using with NodeModify to prevent from node modification events (save command TimeCost)
        with slicer.util.NodeModify(nodeSeq_Landmarks):
            # 03. Fill up the SequenceNode with empty 'PointList'
            num_DataNodes = nodeSeqBrowser.GetNumberOfItems()
            nodeSeq_LinearTransform = nodeSeqBrowser.GetSequenceNode(slicer.util.getNode(STR_NodeName_SeqBrowserProxy_LinearTransform))
            for idx_DataNode in range(num_DataNodes):
                str_IndexValue_Time = nodeSeq_LinearTransform.GetNthIndexValue(idx_DataNode)
                emptyPointList = slicer.vtkMRMLMarkupsFiducialNode()
                emptyPointList.SetAttribute(STR_AttriName_NodePointList_isNegativeFrame, STR_FALSE)
                nodeSeq_Landmarks.SetDataNodeAtValue(emptyPointList, str_IndexValue_Time)
            # 04. Link  nodeSequence and node_SeqBrowserProxy_Landmarks   to nodeSeqBrowser
            nodeSeqBrowser.AddProxyNode(node_SeqBrowserProxy_Landmarks, nodeSeq_Landmarks, False)

        print(f'\t\t Initialized nodeSeq_Landmarks {nodeSeq_Landmarks.GetName()}.GetID() = {nodeSeq_Landmarks.GetID()}')
        return nodeSeq_Landmarks

    # ------------------------------------------------------------------------------------------------------------------
    def setVisibility_and_AddDisplayNodeObserver(self, nodeLandmarkCurve_Target):
        # Set up DisplayNode    &   Attach Mouse Hover Observer
        nodeDiaplay_Curve_Target = nodeLandmarkCurve_Target.GetDisplayNode()
        nodeDiaplay_Curve_Target.SetVisibility2D(False)                 # Never show in 2D
        nodeDiaplay_Curve_Target.SetPropertiesLabelVisibility(False)    # Hide Curve's Name
        nodeDiaplay_Curve_Target.SetPointLabelsVisibility(False)    # Show CurveControlPoint's Label when hide 2D Scan
        self.AddObserver_nodeDisplay_Curve(nodeDiaplay_Curve_Target)

    def createNewNode_LandmarkCurve(self, nodeSeqBrowser_Target, str_LandmarkCurveType_Target):
        ''' **Logic.createNewNode_LandmarkCurve(self, nodeSeqBrowser_Target, str_LandmarkType_Target) ''' ''''''
        # 01. Get NodeName
        strNodeName_LandmarkCurve = self.obtainStrNodeName_LandmarkCurve(nodeSeqBrowser_Target.GetName(), str_LandmarkCurveType_Target)
        # 02. Add NewNode to the mrmlScene
        nodeLandmarkCurve_Target = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", strNodeName_LandmarkCurve)

        # anchor = time.time();
        # 03. Link with SeqBrowser using RefRole
        #       03-A. Link from node_SeqBrowser to node_LandmarkCurve
        if str_LandmarkCurveType_Target == STR_LandmarkType_LeftLamina:
            nodeSeqBrowser_Target.SetNodeReferenceID(STR_CurveNode_RefRole_LeftLamina, nodeLandmarkCurve_Target.GetID())
            func_obtainStr_LandmarkLabel = self.obtainStr_LandmarkLabel_LeftLamina
        elif str_LandmarkCurveType_Target == STR_LandmarkType_RightLamina:
            nodeSeqBrowser_Target.SetNodeReferenceID(STR_CurveNode_RefRole_RightLamina,nodeLandmarkCurve_Target.GetID())
            func_obtainStr_LandmarkLabel = self.obtainStr_LandmarkLabel_RightLamina
        elif str_LandmarkCurveType_Target == STR_LandmarkCurveType_SpinalCord:
            nodeSeqBrowser_Target.SetNodeReferenceID(STR_CurveNode_RefRole_SpinalCord, nodeLandmarkCurve_Target.GetID())
            func_obtainStr_LandmarkLabel = self.obtainStr_CurveControlPointLabel_SpinalCord
        else:
            raise ValueError(f'Wrong str_LandmarkCurveType_Target = {str_LandmarkCurveType_Target}')
        # print(f'TimeCost A = {time.time() - anchor: .04f}s'); anchor = time.time()

        # Using with NodeModify to prevent from node modification events (save command TimeCost)
        with slicer.util.NodeModify(nodeLandmarkCurve_Target):
            #   03-B. Link from node_LandmarkCurve to node_SeqBrowser
            nodeLandmarkCurve_Target.SetNodeReferenceID(STR_SeqBrowserNode_RefRole_Parent, nodeSeqBrowser_Target.GetID())

            # 04. Fill up the CurveNode with empty 'PointList' using Array_Initialization + Unset
            #       04-A. Initial the length of CurveNode
            num_TotalFrames = nodeSeqBrowser_Target.GetNumberOfItems()
            arr_EmptyCurvePositions = np.zeros([num_TotalFrames, 3])
            slicer.util.updateMarkupsControlPointsFromArray(nodeLandmarkCurve_Target, arr_EmptyCurvePositions)

            # print(f'TimeCost B = {time.time() - anchor: .04f}s');   anchor = time.time()
            #       04-B. Unset all to make place-holders, Set-Locked to unable to be dragged in 3D
            for idx_ControlPoint in range(num_TotalFrames):
                nodeLandmarkCurve_Target.UnsetNthControlPointPosition(idx_ControlPoint)     # Unset positions
                str_LandmarkLabel = func_obtainStr_LandmarkLabel(nodeSeqBrowser_Target.GetName(), idx_ControlPoint + INT_SliderFrameIndex_Min)
                nodeLandmarkCurve_Target.SetNthControlPointLabel(idx_ControlPoint, str_LandmarkLabel)   # Initial Labels
                nodeLandmarkCurve_Target.SetNthControlPointLocked(idx_ControlPoint, True)   # Lock every ControlPoint
            # print(f'TimeCost C = {time.time() - anchor: .04f}s');  anchor = time.time()

            # 05. Set attribute:  LandmarkType
            nodeLandmarkCurve_Target.SetAttribute(STR_AttriName_LandmarkType, str_LandmarkCurveType_Target)
            # print(f'TimeCost D = {time.time() - anchor: .04f}s');  anchor = time.time()
            # 06. Set attribute:  Visibility.   Show curve only if more than 2 ControlPoints
            nodeLandmarkCurve_Target.SetAttribute(STR_AttriName_isCurve3PointsDisplay, STR_TRUE)   # By default, Set True
            self.updateVisibility_LandmarkCurve_Target(nodeLandmarkCurve_Target)   # Show curve only if more than 2 ControlPoints

        print(f'\tCreate CurveLandmark \t{nodeLandmarkCurve_Target.GetName()}: ID = {nodeLandmarkCurve_Target.GetID()}')
        # 07. Set up DisplayNode    &   Attach Mouse Hover Observer
        self.setVisibility_and_AddDisplayNodeObserver(nodeLandmarkCurve_Target)

        return nodeLandmarkCurve_Target

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section VII:  logicUpdate     &    Functions   that call paramNodeUpdate ====
    # ------------------------------------------------------------------------------------------------------------------
    def setDefaultParameters(self, parameterNode):
        """    SL_Developer, B:    Initialize parameter node, Re-Enter, Re-Load.    """''''''
        print("**Logic.setDefaultParameters(self, parameterNode), \tSL_Developer, B");
        # I. Before  updating the SingleTon ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        wasModified = parameterNode.StartModify()  # Modify all properties in a single batch
        # --------------------------------------------------------------------------------------------------------------
        # II. Update the SingleTon ParameterNode; No updateGUIFromParameterNode triggered in this step
        #       II-01. Set NodeRef for curSelected SeqBrowser, select the first if not selected
        if not parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected):
            node_SeqBrowser_First = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSequenceBrowserNode")
            if node_SeqBrowser_First:
                #   II-01-A. Set NodeRefID for paramNode
                parameterNode.SetNodeReferenceID(STR_SeqBrowserNode_RefRole_Selected, node_SeqBrowser_First.GetID())
                #   II-01-B. Synchronize    with    modules.sequences's    SequenceBrowser active node
                slicer.modules.sequences.widgetRepresentation().setActiveBrowserNode(node_SeqBrowser_First)
        else:
            #       II-01-C.    Already got NodeRefID for paramNode, we only need to Synchronize with  modules.sequences
            nodeSeqBrowser_Selected = parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
            slicer.modules.sequences.widgetRepresentation().setActiveBrowserNode(nodeSeqBrowser_Selected)

        #       II-02. Set NodeRef for ModuleSingleton (existed first) SeqBrowser_ProxyNode_Landmarks, SL_Proxy
        self.paramNodeUpdate_SearchSetModuleSingleton_ProxyNode_Landmarks(parameterNode)
        # --------------------------------------------------------------------------------------------------------------
        # III. After   updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        parameterNode.EndModify(wasModified)

        # if not parameterNode.GetParameter(STR_SeqBrowserNode_RefRole_Selected):
        #   parameterNode.SetParameter(STR_ParameterNode_ParamFloat_Threshold, str(DEFAULT_ParameterNode_ParamFloat))

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # -----------        Section VI-02:     Sub-Functions with prefix/surfix paramNodeUpdate      ----------------------
    # ----- 1. All sub-functions prefix/surfix with paramNodeUpdate;              --------------------------------------
    # ------2. All paramNodeUpdate functions                        canNOT     self.getParameterNode().StartModify() ---
    # ------3. The superior function who call paramNodeUpdate function MUST    self.getParameterNode().StartModify() ---
    # ------------------------------------------------------------------------------------------------------------------
    def paramNodeUpdate_SearchSetModuleSingleton_ProxyNode_Landmarks(self, parameterNode):
        print("\t**Logic.paramNodeUpdate_SearchSetModuleSingleton_ProxyNode_Landmarks(self, nodeSeqBrowser), SL_Proxy");
        # 01. Try to find existing Proxy from nodeSeqBroswer_Selected, and assign to parameterNode
        nodeSeqBroswer_Selected = parameterNode.GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if nodeSeqBroswer_Selected:
            node_ProxyLandmarks = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBroswer_Selected)
            if node_ProxyLandmarks:
                # 01-A. Add Observers designed for SeqBrowserProxy_Landmarks
                self.AddObserver_SeqBrowserProxy_Landmarks(node_ProxyLandmarks)
                # 01-B. Grant ModuleSingleton:  Add Reference to the ParameterNode ->  trigger updateGUIFromParameterNode
                parameterNode.SetNodeReferenceID(STR_pListNode_RefRole_LandmarkProxy, node_ProxyLandmarks.GetID())
                return
        else:
            node_ProxyLandmarks = parameterNode.GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            if node_ProxyLandmarks:
                # 01-A. Add Observers designed for SeqBrowserProxy_Landmarks
                self.AddObserver_SeqBrowserProxy_Landmarks(node_ProxyLandmarks)
                # 01-B. node_ProxyLandmarks doesn't belong to the selected SeqBrowser, we hide Proxy
                node_ProxyLandmarks.SetDisplayVisibility(False)
                return

        # 02. If not found, choose the first existed ProxyNode_Landmarks as ModuleSingleton; same STR_ReferenceRole
        list_SeqBrowserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
        for nodeSeqBrowser in list_SeqBrowserNodes:
            node_SeqBrowserProxy_Landmarks = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser)
            if node_SeqBrowserProxy_Landmarks:
                # 02-A. Add Observers designed for SeqBrowserProxy_Landmarks
                self.AddObserver_SeqBrowserProxy_Landmarks(node_SeqBrowserProxy_Landmarks)
                # 02-B. Grant ModuleSingleton:  Add Reference to the ParameterNode ->  trigger updateGUIFromParameterNode
                parameterNode.SetNodeReferenceID(STR_pListNode_RefRole_LandmarkProxy, node_SeqBrowserProxy_Landmarks.GetID())
                print(f'\t\t\tInitialized ModuleSingleton SeqBrowser_ProxyNode '
                      f'{node_SeqBrowserProxy_Landmarks.GetName()} = {node_SeqBrowserProxy_Landmarks.GetID()}')
                break;
    # ------------------------------------------------------------------------------------------------------------------
    def createNewNode_ProxyLandmarks__paramNodeUpdate(self):
        print("\t**Logic.createNewNode_ProxyLandmarks__paramNodeUpdate(self), SL_Proxy"); test = 0; test += 1
        # 01. Add new node to the scene
        nodePointList_SeqBrowserProxy_Landmarks = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode",
                                                                           STR_NodeName_SeqBrowserProxy_Landmarks)
        # 02. Add Observers designed for SeqBrowserProxy_Landmarks
        self.AddObserver_SeqBrowserProxy_Landmarks(nodePointList_SeqBrowserProxy_Landmarks)

        # 03. Grant ModuleSingleton:     Add Reference to the ParameterNode ->  trigger updateGUIFromParameterNode
        self.getParameterNode().SetNodeReferenceID(STR_pListNode_RefRole_LandmarkProxy, nodePointList_SeqBrowserProxy_Landmarks.GetID())

        return nodePointList_SeqBrowserProxy_Landmarks

    # ------------------------------------------------------------------------------------------------------------------
    def getSafe_ModuleSingleton_ProxyLandmarks__paramNodeUpdate(self):
        print("\t**Logic.getSafe_ModuleSingleton_ProxyLandmarks__paramNodeUpdate(self), SL_Proxy"); test = 0; test += 1
        ''' SL_Notes: in function getSafe_*(), we initialize if the TargetNode did not exist! ''' ''''''
        # 01. Check the existence of nodeModuleSingleton (nMS)
        nMS_SeqBrowserProxy_Landmarks = self.getParameterNode().GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
        # 02. If not existed, we initialize one nodePointList_SeqBrowser_Landmarks and SetReferenceID
        if not nMS_SeqBrowserProxy_Landmarks:
            nMS_SeqBrowserProxy_Landmarks = self.createNewNode_ProxyLandmarks__paramNodeUpdate()
            print(f'\t\t\tInitialized ModuleSingleton SeqBrowser_ProxyNode_Landmark '
                  f'{nMS_SeqBrowserProxy_Landmarks.GetName()} = {nMS_SeqBrowserProxy_Landmarks.GetID()}')
        return nMS_SeqBrowserProxy_Landmarks

    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section VIII:    Other Logic Functions        ===============================
    # ------------------------------------------------------------------------------------------------------------------
    # ---------------  Section VIII-01:     Boolean (is_)     Functions          ---------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def isValid_idxTargetFrame(self, nodeSeqBrowser, idx_TargetFrame):
        ''' **Logic.isValid_idxTargetFrame(self, nodeSeqBrowser, idx_TargetFrame) ''' ''''''
        if nodeSeqBrowser and idx_TargetFrame >=0 and idx_TargetFrame < nodeSeqBrowser.GetNumberOfItems():
            return True;
        else:
            return False

    def isUserLabeling_InteractionSingleton_PlaceMode(self):
        node_InteractionSingleton = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        return node_InteractionSingleton.GetCurrentInteractionMode() == slicer.vtkMRMLInteractionNode.Place

    def isPlaceModePersistent(self):
        node_InteractionSingleton = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        return node_InteractionSingleton.GetPlaceModePersistence()

    # ------------------------------------------------------------------------------------------------------------------
    # ---------------  Section VIII-02:     Set / Update      Functions          ---------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def setProxyNode_Landmarks_to_SeqBrowser(self, nodeSeqBrowser, node_SeqBrowserProxy_Landmarks):
        print("\t**Logic.setProxyNode_Landmarks_to_SeqBrowser(self)");  test = 0; test += 1

        # 01. Set Reference:  using ReferenceRole and nodeID  for nodeSeqBrowser! Important step!
        nodeSeqBrowser.SetNodeReferenceID(STR_pListNode_RefRole_LandmarkProxy, node_SeqBrowserProxy_Landmarks.GetID())

        # 02. TimeCost 0.25s!   Create SequenceNode:  nodeSeq_Landmarks   for     node_SeqBrowserProxy_Landmarks
        nodeSeq_Landmarks_Old = nodeSeqBrowser.GetSequenceNode(node_SeqBrowserProxy_Landmarks)
        if not nodeSeq_Landmarks_Old:
            self.createNewNode_SequenceLandmarks(nodeSeqBrowser, node_SeqBrowserProxy_Landmarks)
        elif nodeSeqBrowser.GetNumberOfItems() != nodeSeq_Landmarks_Old.GetNumberOfDataNodes():
            print(f'\tOld nodeSeq_Landmarks_Old.GetNumberOfDataNodes = {nodeSeq_Landmarks_Old.GetNumberOfDataNodes()}')
            nodeSeqBrowser.RemoveSynchronizedSequenceNode(nodeSeq_Landmarks_Old.GetID())
            slicer.mrmlScene.RemoveNode(nodeSeq_Landmarks_Old)
            self.createNewNode_SequenceLandmarks(nodeSeqBrowser, node_SeqBrowserProxy_Landmarks)

        # 03. TimeCost 0.22s! Create All Landmark_Curves for the display of nodeSeq_Landmarks
        for str_LandmakrCurveType in LIST_LandmarkCurveType:
            if str_LandmakrCurveType == STR_LandmarkType_LeftLamina:
                node_LandmarkCurve = nodeSeqBrowser.GetNodeReferenceID(STR_CurveNode_RefRole_LeftLamina)
            elif str_LandmakrCurveType == STR_LandmarkType_RightLamina:
                node_LandmarkCurve = nodeSeqBrowser.GetNodeReferenceID(STR_CurveNode_RefRole_RightLamina)
            elif str_LandmakrCurveType == STR_LandmarkCurveType_SpinalCord:
                node_LandmarkCurve = nodeSeqBrowser.GetNodeReferenceID(STR_CurveNode_RefRole_SpinalCord)
            if not node_LandmarkCurve:
                self.createNewNode_LandmarkCurve(nodeSeqBrowser, str_LandmakrCurveType)

        # 04. Update visibility of ProxyNode, in case there was one but not visible
        node_SeqBrowserProxy_Landmarks.SetDisplayVisibility(True)  # In case there was one but not visible

    # ------------------------------------------------------------------------------------------------------------------
    def setSeqBrowser_SeqLandmark_SaveChanges_False__TargetSeqBrowser(self, nodeSeqBrowser_Target):
        if not nodeSeqBrowser_Target:
            return
        nodeProxyLandmarks_Target = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser_Target)
        if nodeProxyLandmarks_Target:
            nodeSeq_Landmarks_Target = nodeSeqBrowser_Target.GetSequenceNode(nodeProxyLandmarks_Target)
            nodeSeqBrowser_Target.SetSaveChanges(nodeSeq_Landmarks_Target, False)
            print(f'\tSetSaveChanges( False ), \t nodeSeqBrowser_Target.GetID() = {nodeSeqBrowser_Target.GetID()}')

    def setAllSeqBrowser_SeqLandmark_SaveChanges_False__EmptyProxyNode(self):
        ''' SL_Note:    This function is to prevent Incorrect Landmark Change ''' ''''''
        print("\t .SetSaveChanges(nodeSeq_Landmarks_Target, False)\t **Logic.setAllSeqBrowser_SeqLandmark_SaveChanges_False__EmptyProxyNode(self), SL_Proxy"); test = 0; test += 1

        nodeSeqBrowser_Selected = self.getParameterNode().GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected:
            return
        # 01. Disable SaveChanges before RemoveAll_ProxyNode_ControlPoints
        #       01-A. Have to disable the current SeqBrowser!
        self.setSeqBrowser_SeqLandmark_SaveChanges_False__TargetSeqBrowser(nodeSeqBrowser_Selected)
        #       01-B. Disable all SeqBrowser
        list_SeqBrowserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
        for nodeSeqBrowser in list_SeqBrowserNodes:
            self.setSeqBrowser_SeqLandmark_SaveChanges_False__TargetSeqBrowser(nodeSeqBrowser)

        # 02. RemoveAll_ProxyNode_ControlPoints after SetFalse of SaveChanges
        for nodeSeqBrowser in list_SeqBrowserNodes:
            node_ProxyLandmarks = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser)
            if node_ProxyLandmarks:
                node_ProxyLandmarks.RemoveAllControlPoints()
                print(f'\tRemoveAllControlPoints, \t nodeSeqBrowser.GetID() = {nodeSeqBrowser.GetID()}')

    # ------------------------------------------------------------------------------------------------------------------
    def updateVisibility_ProxyNode_Landmark(self, nodeTarget_SeqBrowser):
        print("**Logic.updateVisibility_ProxyNode_Landmark(self, nodeTarget_SeqBrowser), SL_Proxy");
        if not nodeTarget_SeqBrowser:
            # No SeqBrowser Selected, no scene or module not entered; we try to find ProxyNode directly
            node_ProxyLandmarks = self.getParameterNode().GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
            if node_ProxyLandmarks:
                node_ProxyLandmarks.SetDisplayVisibility(False)
        else:
            # There is SeqBrowser Selected, we need to check ProxyNode from the nodeSeqBrowser_Selected
            node_ProxyLandmarks = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeTarget_SeqBrowser)
            if node_ProxyLandmarks:
                node_ProxyLandmarks.SetDisplayVisibility(True)
            else:
                # SeqBrowser does not contain Sequence Landmark, we need hide existed (ModuleSingleton) ProxyNode
                nMS_ProxyLandmarks = self.getParameterNode().GetNodeReference(STR_pListNode_RefRole_LandmarkProxy)
                if nMS_ProxyLandmarks:
                    nMS_ProxyLandmarks.SetDisplayVisibility(False)

    # ------------------------------------------------------------------------------------------------------------------
    def logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(self, idx_TargetFrame):
        ''' **Logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex(self, idx_TargetFrame) ''' ''''''
        # 00-A. Check the validity of nodeSeqBrowser_Selected and idx_TargetFrame
        nodeSeqBrowser_Selected = self.getParameterNode().GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected:     return
        # 00-B. Check the validity of idx_TargetFrame
        if not self.isValid_idxTargetFrame(nodeSeqBrowser_Selected, idx_TargetFrame):
            raise ValueError(f'SL_Alert! Invalid idx_TargetFrame = {idx_TargetFrame}');    return

        # 01. Update nodeSeqBrowser along with its the Current-SelectedItemNumber
        nodeSeqBrowser_Selected.SetSelectedItemNumber(idx_TargetFrame)
        print(f"\t\t**Logic.logicUpdate_SwitchSelection_SelectedSeqBrowser_ChangeFrameIndex()\t"
            f"nodeSeqBrowser_Selected.GetID() = {nodeSeqBrowser_Selected.GetID()}, idx_TargetFrame = {idx_TargetFrame}")

    # ------------------------------------------------------------------------------------------------------------------
    def obtain__IdxToInsert_isUnsertNeeded__Dichotomy(self, nodeCurve_Target, idxFrame_Target):
        # 00. Return 0  if zero ControlPoint
        if nodeCurve_Target.GetNumberOfControlPoints() == 0:
            idx_ToInsert = 0;   isUnsetNeeded = False
            return idx_ToInsert, isUnsetNeeded
        # 01. Initial Test
        #       01-A. Initial idx_LeftControlPoint, idx_RightControlPoint and idx_Agent
        idx_ControlPoint_Left   = 0
        idx_ControlPoint_Right  = nodeCurve_Target.GetNumberOfControlPoints() - 1  # Python index starts from 0
        idx_ControlPoint_Agent  = nodeCurve_Target.GetLastUsedControlPointNumber()
        idx_ControlPoint_Agent  = min(idx_ControlPoint_Agent, idx_ControlPoint_Right)
        idx_ControlPoint_Agent  = max(idx_ControlPoint_Agent, idx_ControlPoint_Left)
        #       01-B. Intial    strLabel_Left,  idxFrame_Right     and     idxFrame_Agent
        strLabel_Left   = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Left)
        strLabel_Right  = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Right)
        strLabel_Agent  = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Agent)
        _, idxFrame_Left = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Left)
        _, idxFrame_Right = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Right)
        _, idxFrame_Agent = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Agent)
        #       01-C. Check to return or not with the Initial Test
        if idxFrame_Target == idxFrame_Left:            return idx_ControlPoint_Left, True
        if idxFrame_Target == idxFrame_Right:           return idx_ControlPoint_Right, True
        if idxFrame_Target < idxFrame_Left:             return 0, False
        if idxFrame_Target > idxFrame_Right:            return idx_ControlPoint_Right + 1, False

        if idxFrame_Target == idxFrame_Left + 1:
            idx_ControlPoint_LeftPlus = idx_ControlPoint_Left + 1
            strLabel_LeftPlus = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_LeftPlus)
            _, idxFrame_LeftPlus = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_LeftPlus)
            return idx_ControlPoint_LeftPlus, idxFrame_Target == idxFrame_LeftPlus
        if idxFrame_Target == idxFrame_Right - 1:
            idx_ControlPoint_RightMinus = idx_ControlPoint_Right - 1
            strLabel_RightMinus = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_RightMinus)
            _, idxFrame_RightMinus = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_RightMinus)
            return idx_ControlPoint_RightMinus, idxFrame_Target == idxFrame_RightMinus

        # 02. Dichotomy Search
        while True:
            # 02-A. Check to return or not
            if idxFrame_Target == idxFrame_Agent:           return idx_ControlPoint_Agent,  True

            if idxFrame_Target == idxFrame_Agent + 1:
                idx_ControlPoint_AgentPlus = idx_ControlPoint_Agent + 1
                strLabel_AgentPlus = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_AgentPlus)
                _, idxFrame_AgentPlus = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_AgentPlus)
                return idx_ControlPoint_AgentPlus, idxFrame_Target == idxFrame_AgentPlus
            if idxFrame_Target == idxFrame_Agent - 1:
                idx_ControlPoint_AgentMinus = idx_ControlPoint_Agent - 1
                strLabel_AgentMinus = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_AgentMinus)
                _, idxFrame_AgentMinus = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_AgentMinus)
                return idx_ControlPoint_AgentMinus, idxFrame_Target == idxFrame_AgentMinus

            # 02-B. Squeeze range [idx_ControlPoint_Left,  idx_ControlPoint_Right]  and     update  idxFrame_Agent
            if idxFrame_Agent < idxFrame_Target:
                idx_ControlPoint_Left   = idx_ControlPoint_Agent
                strLabel_Left = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Left)
                _, idxFrame_Left = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Left)
            elif idxFrame_Agent > idxFrame_Target:
                idx_ControlPoint_Right  = idx_ControlPoint_Agent
                strLabel_Right = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Right)
                _, idxFrame_Right = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Right)
            else:   raise ValueError(f'idxFrame_Agent = {idxFrame_Agent}, idxFrame_Target = {idxFrame_Target}')

            idx_ControlPoint_Agent = int(0.5 * (idx_ControlPoint_Left + idx_ControlPoint_Right))
            strLabel_Agent = nodeCurve_Target.GetNthControlPointLabel(idx_ControlPoint_Agent)
            _, idxFrame_Agent = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_Agent)

            # 02-C. Check if range [idx_ControlPoint_Left,  idx_ControlPoint_Right] cannot be squeezed anymore
            if idx_ControlPoint_Agent == idx_ControlPoint_Left or idx_ControlPoint_Agent == idx_ControlPoint_Right:
                return idx_ControlPoint_Right, False

    # ------------------------------------------------------------------------------------------------------------------
    def updateOneCurve_OneControlPoint__Dichotomy(self, nodeCurve_Target, idxFrame_Target, vtkVec3d_RAS_WorldPosition_Target, strLabel_Target):
        ''' **Logic.updateOneCurve_OneControlPoint__Dichotomy(self, nodeCurve, idxFrame, vtkVec3d_RAS_WorldPosition, strLabel) ''' #
        # 00. Case No ControlPoint before
        if nodeCurve_Target.GetNumberOfControlPoints() == 0:
            idx_ToInsert = 0;
        else:
            # 01. Locate idx_ToInsert using dichotomy
            idx_ToInsert, isUnsetNeeded = self.obtain__IdxToInsert_isUnsertNeeded__Dichotomy(nodeCurve_Target, idxFrame_Target)
            # 02. If idxFrame_Target ControlPoint existed, Unset the existed ControlPoint
            if isUnsetNeeded:
                # nodeCurve_Target.UnsetNthControlPointPosition(idx_ToInsert)
                nodeCurve_Target.RemoveNthControlPoint(idx_ToInsert)

        # 03. Insert the TargetControlPoint
        nodeCurve_Target.InsertControlPoint(idx_ToInsert, vtkVec3d_RAS_WorldPosition_Target, strLabel_Target)
        # 04. Lock the NewlyInserted Point
        nodeCurve_Target.SetNthControlPointLocked(idx_ToInsert, True)
        # 05. Update Visibility:    display the curve only if there are more than 3 points
        self.updateVisibility_LandmarkCurve_Target(nodeCurve_Target)

    # ------------------------------------------------------------------------------------------------------------------
    def updateVisibility_LandmarkCurve_Target(self, nodeLandmarkCurve_Target):
        ''' **Logic.updateVisibility_LandmarkCurve_Target(self, nodeLandmarkCurve_Target) ''' #
        str_isCurve3PointDisplay = nodeLandmarkCurve_Target.GetAttribute(STR_AttriName_isCurve3PointsDisplay)
        nodeLandmarkCurve_Target.SetDisplayVisibility(False)
        if str_isCurve3PointDisplay == STR_TRUE:
            if nodeLandmarkCurve_Target.GetNumberOfDefinedControlPoints() >= 2:
                # Show curve only if more than 3 ControlPoints
                nodeLandmarkCurve_Target.SetDisplayVisibility(True)

    # ------------------------------------------------------------------------------------------------------------------
    def updateVisibility_LandmarkCurves_ShowOnlySelectedSeqBrowser(self):
        ''' **Logic.updateVisibility_LandmarkCurves_ShowOnlySelectedSeqBrowser(self) ''' #
        nodeSeqBrowser_Selected = self.getParameterNode().GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        list_SeqBrowserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
        for nodeSeqBrowser in list_SeqBrowserNodes:
            nodeCurve_Left  = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
            nodeCurve_Right = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
            nodeCurve_SpinalCord = nodeSeqBrowser.GetNodeReference(STR_CurveNode_RefRole_SpinalCord)
            if nodeCurve_Left:      nodeCurve_Left.SetDisplayVisibility(nodeSeqBrowser == nodeSeqBrowser_Selected)
            if nodeCurve_Right:     nodeCurve_Right.SetDisplayVisibility(nodeSeqBrowser == nodeSeqBrowser_Selected)
            if nodeCurve_SpinalCord:nodeCurve_SpinalCord.SetDisplayVisibility(nodeSeqBrowser == nodeSeqBrowser_Selected)

    # ------------------------------------------------------------------------------------------------------------------
    def updateCurves_UnsetTargetFrameLandmark(self, node_SeqBrowser, idx_TargetFrame):
        ''' **Logic.updateVisibility_LandmarkCurves_ShowOnlySelectedSeqBrowser(self) ''' #
        nodeCurve_Left = node_SeqBrowser.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
        nodeCurve_Right = node_SeqBrowser.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
        nodeCurve_SpinalCord = node_SeqBrowser.GetNodeReference(STR_CurveNode_RefRole_SpinalCord)

        nodeCurve_Left.UnsetNthControlPointPosition(idx_TargetFrame)
        nodeCurve_Right.UnsetNthControlPointPosition(idx_TargetFrame)
        nodeCurve_SpinalCord.UnsetNthControlPointPosition(idx_TargetFrame)
        self.updateVisibility_LandmarkCurve_Target(nodeCurve_Left)  # Check if more than 2 ControlPoints
        self.updateVisibility_LandmarkCurve_Target(nodeCurve_Right)  # Check if more than 2 ControlPoints
        self.updateVisibility_LandmarkCurve_Target(nodeCurve_SpinalCord)  # Check if more than 2 ControlPoints

    # ------------------------------------------------------------------------------------------------------------------
    def updateCurves_FrameLandmarks__on_ProxyControlPointUpdate(self, nodeSeqBrowser_Target, nodePointList_Target):
        ''' **Logic.updateCurves_FrameLandmarks__on_ProxyControlPointUpdate(self, nodePointList_Target) 
                This function update the Landmark_Curves using Cur-Frame-of-ControlPoints from nodePointList_Target.
        ''' ''''''
        num_ControlPoints = nodePointList_Target.GetNumberOfControlPoints()
        if num_ControlPoints <= 0 or num_ControlPoints > len(LIST_LANDMARK_TYPE) + 1: # +1 for case Undefined / Preview
            raise ValueError(f'SL_Alert! Should not be called, num_ControlPoints = {num_ControlPoints}')

        for idxControlPoint_PointList in range(num_ControlPoints):
            if nodePointList_Target.GetNthControlPointPositionStatus(idxControlPoint_PointList)  \
                        == slicer.vtkMRMLMarkupsNode.PositionDefined:
                self.updateCurves_OneLandmark_CurFrame(nodeSeqBrowser_Target, nodePointList_Target, idxControlPoint_PointList)

    # ------------------------------------------------------------------------------------------------------------------
    def updateCurves_OneLandmark_CurFrame(self, nodeSeqBrowser_Target, nodePointList_Target, idxControlPoint_PointList_Target):
        ''' **Logic.updateCurves_OneLandmark_CurFrame(self, nodePointList_Target) ''' ''''''
        num_ControlPoints = nodePointList_Target.GetNumberOfControlPoints()
        if idxControlPoint_PointList_Target < 0 or idxControlPoint_PointList_Target >= num_ControlPoints:
            raise ValueError(f'SL_Alert! idxControlPoint_PointList_Target = {idxControlPoint_PointList_Target}')

        # 01. Get LandmarkType and idxFrame from nodeSeqBrowser_Target
        strLabel_ControlPoint = nodePointList_Target.GetNthControlPointLabel(idxControlPoint_PointList_Target)
        str_LabelPrefix, idxFrame = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(strLabel_ControlPoint)
        # 02. Verify idxFrame with nodeSeqBrowser_Target
        if not idxFrame == nodeSeqBrowser_Target.GetSelectedItemNumber():
            raise ValueError(f'strLabel_ControlPoint = {strLabel_ControlPoint}, \t '
                    f'nodeSeqBrowser_Target.GetSelectedItemNumber() = {nodeSeqBrowser_Target.GetSelectedItemNumber()}')
        # 03. Get nodeCurve_Target Landmark
        if str_LabelPrefix == STR_ControlPointLabelPrefix_Left:
            nodeCurve_Target = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
        elif str_LabelPrefix == STR_ControlPointLabelPrefix_Right:
            nodeCurve_Target = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
        else:  raise ValueError(f'str_LabelPrefix = {str_LabelPrefix}') # Should ot be SpinalCord
        # 04-A. Update nodeCurve_Target     &   curveSpinalCord is applicable
        vtkVec3d_RAS_WorldPosition = nodePointList_Target.GetNthControlPointPositionVector(idxControlPoint_PointList_Target)
        self.updateCurves_OneLandmark_TargetFrame_GivenRAS(nodeSeqBrowser_Target, idxFrame, str_LabelPrefix, vtkVec3d_RAS_WorldPosition)

    # ------------------------------------------------------------------------------------------------------------------
    def updateCurves_OneLandmark_TargetFrame_GivenRAS(self, nodeSeqBrowser_Target, idx_TargetFrame, str_LandmarkPrefix, vec_RAS_WorldPosition):
        ''' **Logic.updateCurves_OneLandmark_CurFrame(self, nodePointList_Target) ''' ''''''
        # 00-A. Check the validity of nodeSeqBrowser_Selected and idx_TargetFrame
        if (not nodeSeqBrowser_Target) or (not self.isValid_idxTargetFrame(nodeSeqBrowser_Target, idx_TargetFrame)):
            raise ValueError(f'SL_Alert! Invalid idx_TargetFrame = {idx_TargetFrame}');    return
        # 00-B. Check if SeqBrowser has landmarks
        if self.hasLandmarks_inTargetNode_SeqBrowser(nodeSeqBrowser_Target) == False:
            raise ValueError(f'SL_Alert! nodeSeqBrowser_Target = {nodeSeqBrowser_Target}, no Landmark!'); return
        # 00-C. Check validity of   str_LandmarkPrefix
        if not (str_LandmarkPrefix in LIST_LANDMARK_PREFIX):
            raise ValueError(f'SL_Alert!  str_LandmarkPrefix = {str_LandmarkPrefix} !!'); return
        # 00-D. Check shape of vec_RAS_WorldPosition
        if len(vec_RAS_WorldPosition) != NumVar_NumpyLandmark_RAS:
            raise ValueError(f'SL_Alert!  vec_RAS_WorldPosition.shape = {vec_RAS_WorldPosition.shape} !!'); return
        # 00-E. Check the validity of vec_RAS_WorldPosition
        if vec_RAS_WorldPosition[0] == INT_DEFAULT_RAS_VALUE or vec_RAS_WorldPosition[0] == INT_NEGATIVE_RAS_VALUE:
            raise ValueError(f'SL_Alert!  vec_RAS_WorldPosition = {vec_RAS_WorldPosition} !!'); return

        # 01. Determine     nodeCurve_Target    &   nodeCurve_Opposite
        if str_LandmarkPrefix == STR_ControlPointLabelPrefix_Left:
            nodeCurve_Target    = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
            nodeCurve_Opposite  = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
        elif str_LandmarkPrefix == STR_ControlPointLabelPrefix_Right:
            nodeCurve_Target    = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_RightLamina)
            nodeCurve_Opposite  = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_LeftLamina)
        else:  raise ValueError(f'str_LandmarkPrefix = {str_LandmarkPrefix}')

        # 02. Update nodeCurve_Target
        nodeCurve_Target.SetNthControlPointPosition(idx_TargetFrame, vec_RAS_WorldPosition)
        self.updateVisibility_LandmarkCurve_Target(nodeCurve_Target)  # display curve only if more than 2 points

        # 03. Update Curve_SpinalCord
        if nodeCurve_Opposite.GetNthControlPointPositionStatus(idx_TargetFrame)  \
                        == slicer.vtkMRMLMarkupsNode.PositionDefined:
            # 03-A. Get middle point of first two ControlPoint
            vtkVec3d_RAS_WorldPosition_Opposite = nodeCurve_Opposite.GetNthControlPointPositionVector(idx_TargetFrame)
            vtkVec3d_RAS_WorldPosition_Middle =  0.5 * (np.array(vtkVec3d_RAS_WorldPosition_Opposite) + np.array(vec_RAS_WorldPosition))
            # 03-B. Update middle point to Curve_SpinalCord
            nodeCurve_SpinalCord = nodeSeqBrowser_Target.GetNodeReference(STR_CurveNode_RefRole_SpinalCord)
            nodeCurve_SpinalCord.SetNthControlPointPosition(idx_TargetFrame, vtkVec3d_RAS_WorldPosition_Middle)
            # 03-C. Update Visibility: display curve only if more than 2 points
            self.updateVisibility_LandmarkCurve_Target(nodeCurve_SpinalCord)

    # ------------------------------------------------------------------------------------------------------------------
    # ---------------  Section VIII-03:     Slots      Functions          ----------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def onPointAdded(self, proxyNode_Landmark=None, event=None):
        ''' **Logic.onPointAdded(self, nodeTarget_SeqBrowser) 
                Called everytime whenever proxyNode_Landmark got additional ControlPoint:
                    1. Added by user:           One DropLandmark button was triggered, and a ControlPoint was dropped;
                    2. Added by SequenceUpdate: Whenever the is a change of SewBrowser SelectedItem.      ''' ''''''
        # 00-A. Check the validity of nodeSeqBrowser_Selected
        nodeSeqBrowser_Selected = self.getParameterNode().GetNodeReference(STR_SeqBrowserNode_RefRole_Selected)
        if not nodeSeqBrowser_Selected or nodeSeqBrowser_Selected.GetNumberOfItems() == 0:
            # Invalid SeqBrowser_Selected or No recorded data in nodeSeqBrowser_Selected:   no need to continue
            return
        # 00-B. Check the validity of Seq_Landmark from SeqBrowser_Selected
        node_ProxyLandmarks_SelectedSeqBrowser = self.obtainProxyNode_Landmarks_from_SeqBrowser(nodeSeqBrowser_Selected)
        if not node_ProxyLandmarks_SelectedSeqBrowser:
            # SL_Note:  Drop-Landmark button was not triggered, no need to continue
            return

        # 01. Set SeqBrowser Sequence_Landmarks' SaveChanges to Positive
        if self.get_isSwitchingSeqBrowser():
            print(f'SwitchSeqBrowser!! \tSwitchSeqBrowser!! \tSwitchSeqBrowser!! \tSwitchSeqBrowser!! ')
        else:
            nodeSeq_Landmarks = nodeSeqBrowser_Selected.GetSequenceNode(node_ProxyLandmarks_SelectedSeqBrowser)
            nodeSeqBrowser_Selected.SetSaveChanges(nodeSeq_Landmarks, True)

        # 02. Set Landmark's label only if isUserLabeling
        idx_SliderCurFrame = self.obtain_idxSliderCurFrame_from_TargetSeqBrowser(nodeSeqBrowser_Selected)
        print(f"\t\t**Logic.onPointAdded(self, nodePointList), \t.SetSaveChanges(nodeSeq_Landmarks, True) \t idx_SliderCurFrame = {idx_SliderCurFrame}");

        idx_NewlyAddedControlPoint = proxyNode_Landmark.GetNumberOfControlPoints() - 1
        if proxyNode_Landmark.GetNthControlPointPositionStatus(idx_NewlyAddedControlPoint)  \
                        != slicer.vtkMRMLMarkupsNode.PositionDefined:
            # Change Label if not PositionDefined
            if self.getUserLandmarkLabeling_strLandmarkType() == STR_LandmarkType_LeftLamina:
                proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint,
                        self.obtainStr_LandmarkLabel_LeftLamina(nodeSeqBrowser_Selected.GetName(), idx_SliderCurFrame))
            elif self.getUserLandmarkLabeling_strLandmarkType() == STR_LandmarkType_RightLamina:
                proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint,
                        self.obtainStr_LandmarkLabel_RightLamina(nodeSeqBrowser_Selected.GetName(), idx_SliderCurFrame))
            elif self.getUserLandmarkLabeling_strLandmarkType() == STR_LabelButton_Sequential:
                # Must use DefinedControlPoints, otherwise, preview ControlPoints can be counted.
                num_DefinedLandmarks = proxyNode_Landmark.GetNumberOfDefinedControlPoints()
                if num_DefinedLandmarks == 0 or num_DefinedLandmarks == len(LIST_LANDMARK_TYPE): # can be 0
                    proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint, \
                        self.obtainStr_LandmarkLabel_LeftLamina(nodeSeqBrowser_Selected.GetName(), idx_SliderCurFrame))
                elif num_DefinedLandmarks == 1:
                    str_ExistedLandmarkLabel = proxyNode_Landmark.GetNthControlPointLabel(0)
                    str_Existed_LabelPrefix, _ = self.obtain__LablePrefix_IdxFrame__from_ControlPointLabel(str_ExistedLandmarkLabel)

                    if str_Existed_LabelPrefix == STR_ControlPointLabelPrefix_Left:
                        proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint,  \
                            self.obtainStr_LandmarkLabel_RightLamina(nodeSeqBrowser_Selected.GetName(), idx_SliderCurFrame))
                    elif str_Existed_LabelPrefix == STR_ControlPointLabelPrefix_Right:
                        proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint,  \
                            self.obtainStr_LandmarkLabel_LeftLamina(nodeSeqBrowser_Selected.GetName(), idx_SliderCurFrame))
                    else:   raise ValueError(f'SL_Alert! str_Existed_LabelPrefix = {str_Existed_LabelPrefix}')

                else:   raise ValueError(f'SL_Alert! num_Landmarks = {num_DefinedLandmarks}')
            else:
                proxyNode_Landmark.SetNthControlPointLabel(idx_NewlyAddedControlPoint, f'Incorrect strLandmarkType!')
                raise ValueError(f'\n\n\t\tstr_TargetLandmarkType = {self.getUserLandmarkLabeling_strLandmarkType()}\n')

    def onPointRemoved(self, proxyNode_Landmark=None, event=None):
        ''' Called when the UserLabeling cancelled (right clicked) a labeling step ''' ''''''
        print(f'\t**Logic.onPointRemoved(self, proxyNode_Landmark=None, event=None)')

    def AddObserver_SeqBrowserProxy_Landmarks(self, nodePointList_SeqBrowserProxy_Landmarks):
        nodePointList_SeqBrowserProxy_Landmarks.AddObserver(slicer.vtkMRMLMarkupsNode.PointAddedEvent,
                                                            self.onPointAdded)

        # nodePointList_SeqBrowserProxy_Landmarks.AddObserver(slicer.vtkMRMLMarkupsNode.PointPositionUndefinedEvent,
        #                                                     self.onPointPositionUndefined)
        # nodePointList_SeqBrowserProxy_Landmarks.AddObserver(slicer.vtkMRMLMarkupsNode.PointRemovedEvent,
        #                                                     self.onPointRemoved)

    # ------------------------------------------------------------------------------------------------------------------
    def onLandmarkCurve_DisplayModified(self, nodeDiaplay_CallerCurve=None, event=None):
        int_ActiveComponentType = nodeDiaplay_CallerCurve.GetActiveComponentType()

        if int_ActiveComponentType == slicer.vtkMRMLMarkupsDisplayNode.ComponentNone:
            # Reset everything
            slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red").SetSliceVisible(True)  # Display 2D Scan
            nodeDiaplay_CallerCurve.SetPropertiesLabelVisibility(False)     # Hide Curve's Name
            nodeDiaplay_CallerCurve.SetPointLabelsVisibility(False)         # Hide ControlPoints' Label
        elif int_ActiveComponentType == slicer.vtkMRMLMarkupsDisplayNode.ComponentControlPoint:
            nodeDiaplay_CallerCurve.SetPointLabelsVisibility(True)          # Show ControlPoints' Label
            nodeDiaplay_CallerCurve.SetPropertiesLabelVisibility(False)     # Hide Curve's Name
            slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red").SetSliceVisible(False)  # Hide 2D Scan
        elif int_ActiveComponentType == slicer.vtkMRMLMarkupsDisplayNode.ComponentLine:
            nodeDiaplay_CallerCurve.SetPropertiesLabelVisibility(True)  # Show Curve's Name
            nodeDiaplay_CallerCurve.SetPointLabelsVisibility(False)     # Hide ControlPoints' Label
            slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red").SetSliceVisible(False)  # Hide 2D Scan
        else:
            print(f'**Logic.onLandmarkCurve_DisplayModified():  \tint_ActiveComponentType = {int_ActiveComponentType}')

    def AddObserver_nodeDisplay_Curve(self, nodeDiaplay_CallerCurve):
        nodeDiaplay_CallerCurve.AddObserver(vtk.vtkCommand.ModifiedEvent,  self.onLandmarkCurve_DisplayModified)
    # ------------------------------------------------------------------------------------------------------------------


    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section X:    To be continued          ======================================
    # ------------------------------------------------------------------------------------------------------------------
    # def logicUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(self, nodeTarget_SeqBrowser):
    #     ''' **Logic.logicUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(self, nodeTarget_SeqBrowser) '''''''''
    #     # 00. Check the validity of nodeSeqBrowser_Selected and idx_TargetFrame
    #     if not nodeTarget_SeqBrowser:
    #         return


    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        print("**Logic.process(self, inputVolume, outputVolume, imageThreshold, ...)"); test = 0; test += 1
        """   Run the processing algorithm.    Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """''''''
        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        pass

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')



''' ================================================================================================================='''
#
# sl_01__LaminaLandmark_LabelingTest
#
class sl_01__LaminaLandmark_LabelingTest(ScriptedLoadableModuleTest):
    """  This is the test case for your scripted module.
            Uses ScriptedLoadableModuleTest base class, available at:
                https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py  """
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.    """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.    """
        self.setUp()
        self.test_sl_01__LaminaLandmark_Labeling1()

    def test_sl_01__LaminaLandmark_Labeling1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        pass

        self.delayDisplay('Test passed')





''' ================================================================================================================='''
'''   GUI notes:
  1. sequenceSelector:    
      a. Uncheck  qMRMLNodeCombox->addEnabled;    # To label landmarks ONLY, instead of editing the sequenceBrowsers
      b. Uncheck  qMRMLNodeCombox->removeEnabled; # To label landmarks ONLY, instead of editing the sequenceBrowsers
      c. Fill:    qMRMLNodeCombox->nodeTypes = "vtkMRMLSequenceBrowserNode"
      d. Unchek   qMRMLNodeCombox->showChildNodeTypes   # Not sure why!!
      e. Check:   qMRMLNodeCombox->selectNodeUponCreation
'''
''' ================================================================================================================='''
'''SL_Developer:  What need to be done to add new a QT widget into the Module Layout
------------------------------------------------------------------------------------------------------------------------
0.	UI/**.ui	:		Connecting 	the mrmlSceneChanged(vtkMRMScene*) 	signal 	of the top-level widget 
						to 			the setMRMLScene(vtkMRMLScene*) 	slot 	of the widget
------------------------------------------------------------------------------------------------------------------------						
A. 	Signal-Slot         of ui / widgets:  
        To do:    Connect Signal-Slot of all ui.Widgets, to self.updateParameterNodeFromGUI__Set_RefRoleNodeID, or to User-Funcs.
                      Function:             **Widget.setup(self)
                      Widgets: 
                          * Node-Selectors  (qMRMLNodeComboBox)
                          * Sliders         (ctkSliderWidget)
                          * CheckBox        (QCheckBox)
                          * Buttons         (QPushButton)
------------------------------------------------------------------------------------------------------------------------
B. 	Default Selectors 	of ui / widgets:							
        To do:  Developer-Initial, Select default input if nothing is selected yet, to save clicks for the user
		            Function:               **Widget.initializeParameterNode(self):
		            Widgets:          
		                  * Node-Selectors  (qMRMLNodeComboBox)
------------------------------------------------------------------------------------------------------------------------							
C.	Default Values		of SingleTon ParameterNode:						
		To do:  Initialize parameter node with default settings
		            Function:               **Logic.setDefaultParameters(self, parameterNode)
------------------------------------------------------------------------------------------------------------------------
D. 	Update 				UI widgets:								
                    Function:               **Widget.updateGUIFromParameterNode(self, ...)
                    Widgets: 
                          * Node-Selectors  (qMRMLNodeComboBox)
                          * Sliders         (ctkSliderWidget)
                          * CheckBox        (QCheckBox)
                          * Buttons         (QPushButton)
------------------------------------------------------------------------------------------------------------------------
E.	Update	Values		of SingleTon ParameterNode:					
                    Function:               **Widget.updateParameterNodeFromGUI__Set_RefRoleNodeID(self, ...)
                    Widgets: 
                          * Node-Selectors  (qMRMLNodeComboBox)
                          * Sliders         (ctkSliderWidget)
                          * CheckBox        (QCheckBox)
------------------------------------------------------------------------------------------------------------------------
F.	UI Interaction Functions 		of ui / widgets:				
                    Function:               **Widget.onApplyButton(self)
                    Widgets:
                          * Buttons         (QPushButton)
                    Signal / Slot:          self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
------------------------------------------------------------------------------------------------------------------------
G. 	Non-UI Logic Process Functions:									**Logic.process(self, ...)
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
'''
'''=====================================================================================================================
Slicer QT widgets'	SL__Notes:

1. slicer.qMRMLNodeComboBox():		https://apidocs.slicer.org/v5.0/classqMRMLNodeComboBox.html
      ------------------------------------------------------------------------------------------------------------------
      SL_Developer, D:	updateGUIFromParameterNode(self, ...)
          Before 	self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume")):	
                --------------------------------------------------------------------------------------------------------
                self._parameterNode.GetNumberOfNodeReferenceRoles()			== 0
                self.ui.inputSelector.nodeCount() 							== 0
          --------------------------------------------------------------------------------------------------------------
          After 	self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume")):	
                --------------------------------------------------------------------------------------------------------
                type(self._parameterNode.GetNodeReference("InputVolume"))	== 	<class 'NoneType'>
                self._parameterNode.GetNumberOfNodeReferenceRoles()			== 	1
                self._parameterNode.GetNthNodeReferenceRole(0)				== 	'InputVolume'			# Newly added
                type(self._parameterNode.GetNthNodeReferenceRole(1))		==	<class 'NoneType'>
                self.ui.inputSelector.nodeCount()							== 	0
                self.ui.outputSelector.nodeCount()							== 	0
                type(self.ui.outputSelector.currentNode())					==	<class 'NoneType'>
                --------------------------------------------------------------------------------------------------------
                self._parameterNode.GetParameter("Threshold")				== 	'100.0'
                type(self._parameterNode.GetParameter("Threshold")) 		== 	<class 'str'>
                self._parameterNode.GetParameter('Invert')					==	'false'
                type(self._parameterNode.GetParameter('Invert'))			==	<class 'str'>
          --------------------------------------------------------------------------------------------------------------		
E.g., OutputVolume-NodeSelector:		Code-Only 					vs 				UI/**.ui

self.outputSelector = slicer.qMRMLNodeComboBox()						Fill:		QObject->objectName 		= outputSelector	
self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]				Select:		qMRMLNodeCombox->nodeTypes 	= vtkMRMLScalarVolumeNode
self.outputSelector.selectNodeUponCreation = True						InCode:					
                                        firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
                                        if firstVolumeNode:
                                            self._parameterNode.SetNodeReferenceID(STR_ReferenceRole_VolumeInput, firstVolumeNode.GetID())
self.outputSelector.noneEnabled = TrueCheck:							Check:		qMRMLNodeCombox->noneEnabled
self.outputSelector.addEnabled = True									Check:		qMRMLNodeCombox->addEnabled
self.outputSelector.removeEnabled = True								Check:		qMRMLNodeCombox->removeEnabled
self.outputSelector.showHidden = False									Un-Check:	qMRMLNodeCombox->showHidden
self.outputSelector.showChildNodeTypes = False							Un-Check:	qMRMLNodeCombox->showChildNodeTypes
self.outputSelector.setMRMLScene( slicer.mrmlScene )					InCode:		uiWidget.setMRMLScene(slicer.mrmlScene)
self.outputSelector.setToolTip( "Pick the output to the algorithm." )	Fill:		QWidget->toolTip = 'Pick the output to the algorithm.'
parametersFormLayout.addRow("Output Volume: ", self.outputSelector)		Label added in the Qt ui Designer
====================================================================================================================='''
''' ================================================================================================================='''
''' SL__Tutorial:         Slicer Pipeline (Module, Widget, Logic)

I. Module Initial Entry:
	1. **Widget.__init__(self, parent=None)
          self.logic = None
          self._parameterNode = None
          self._updatingGUIFromParameterNode = False
	2. **Widget.setup(self)
	3. **Widget.enter(self)			# Called when users open the module the first time and the widget is initialized
          self.initializeParameterNode(self)
              ---------------------------------------------------------------------------------------------------------
              self.setParameterNode(self.logic.getParameterNode())
                    ---------------------------------------------------------------------------------------------------
                    self.logic.setDefaultParameters(inputParameterNode)
                        -----------------------------------------------------------------------------------------------
                            inputParameterNode.GetAttribute('ModuleName'):	Out[23]: 'sl_01__LaminaLandmark_Labeling'
                            SingleTon ParameterNode:
                                ID: 			vtkMRMLScriptedModuleNodesl_01__LaminaLandmark_Labeling
                                ClassName: 		vtkMRMLScriptedModuleNode
                                Name: 			sl_01__LaminaLandmark_Labeling
                                Debug: 			false
                                Description: 	(none)
                                SingletonTag: 	sl_01__LaminaLandmark_Labeling
                                HideFromEditors: true
                                Selectable: 	true
                                Selected: 		false
                                UndoEnabled: 	false
                                Attributes:
                                    ModuleName:	sl_01__LaminaLandmark_Labeling
                                ModuleName: 	(none)

                            inputParameterNode.GetAttributeNames()	:	Out[20]: ('ModuleName',)
                            inputParameterNode.IsSingleton()		:	Out[37]: True
                            inputParameterNode.GetSingletonTag()	:	'sl_01__LaminaLandmark_Labeling'

                        -----------------------------------------------------------------------------------------------
                        inputParameterNode.SetParameter(STR_ParameterNode_ParamFloat_Threshold, "100.0")
                            inputParameterNode.GetParameterNames():			  ('Threshold',)
                        inputParameterNode.SetParameter(STR_ParameterNode_ParamBool_Invert, STR_FALSE)
                            inputParameterNode.GetParameter('Threshold')：    '100.0',  type == <class 'str'>
                            inputParameterNode.GetParameterNames():			  ('Invert', 'Threshold')
                    ---------------------------------------------------------------------------------------------------
                    self._parameterNode = inputParameterNode
                    self.updateGUIFromParameterNode()
                            self._updatingGUIFromParameterNode = True
              ---------------------------------------------------------------------------------------------------------

II. Switch to other Module / Quit current Module
	**Widget.exit(self)

III. Module Re-Entry:
	**Widget.enter(self):
          self.initializeParameterNode(self)
                  -----------------------------------------------------------------------------------------------------
                  self.setParameterNode(self.logic.getParameterNode())
                          self.logic.setDefaultParameters(inputParameterNode)
                          self.updateGUIFromParameterNode()

IV. Module Re-Load:
	1. 	**Widget.cleanup(self)
	2.	**Widget.__init__(self, parent)
	3. 	**Widget.setup(self)
			self.initializeParameterNode(self)
				  -----------------------------------------------------------------------------------------------------
				  self.setParameterNode(self.logic.getParameterNode())
							self.logic.setDefaultParameters(inputParameterNode)
							self.updateGUIFromParameterNode()
'''