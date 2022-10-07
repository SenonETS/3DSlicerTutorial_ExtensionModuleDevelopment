import logging
import vtk, qt

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import numpy as np

'''=================================================================================================================='''
'''=================================================================================================================='''
'''------------------------- STRING Macro of  sl__US_SeqViewer ------------------------------------------------------'''
'''------------------------------------------------------------------------------------------------------------------'''
INT_SliderFrameIndex_Min                = 1       # StartingValue of slider_FrameIndex, increase from 1
INT_FRAME_INDEX_SLIDER_DEFAULT          = 50      # Default slider_FrameIndex value
INT_FRAME_INDEX_SLIDER_DEFAULT_MAX      = 99      # Default slider_FrameIndex maximum

# ReferenceRole
STR_SeqBrowserNode_RefRole_Selected     = 'SeqBrowser_Ref_CurSelected'



'''=================================================================================================================='''
#
# sl__US_SeqViewer
#
class sl__US_SeqViewer(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "sl__US_SeqViewer"
        self.parent.categories = ["SL_Tutorials"]       # Set categories (the module shows up in the module selector)
        self.parent.dependencies = ["Markups"]          # Add here list of module names that this module requires
        self.parent.contributors = ["Sen Li (École de Technologie Supérieure)"]
        # TODO:     10. update with a link to online module Tutorial
        self.parent.helpText = """This is sl__US_SeqViewer ! """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = 'Step-by-step tutorial on 3D Slicer extension development. ' \
                                          '\nThis file was originally developed by Sen Li, LATIS, École de techonologie supérieure. ' \
                                          '\nSen.Li.1@ens.etsmtl.ca'

        print("sl__US_SeqViewer(ScriptedLoadableModule):    __init__(self, parent)")

'''=================================================================================================================='''
class sl__US_SeqViewerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

    def __init__(self, parent=None):
        """    Called when the user opens the module the first time and the widget is initialized.    """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None  # Singleton initialized through self.setParameterNode(self.logic.getParameterNode())
        self._updatingGUIFromParameterNode = False

        print("**Widget.__init__(self, parent)")

    def setup(self):
        print("**Widget.setup(self), \tSL_Developer")
        """    00. Called when the user opens the module the first time and the widget is initialized. """
        ScriptedLoadableModuleWidget.setup(self)

        # 01. Load widget from .ui file (created by Qt Designer).
        #       Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/sl__US_SeqViewer.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # 02. Set scene in MRML widgets. Make sure that in Qt designer the
        #       top-level qMRMLWidget's   "mrmlSceneChanged(vtkMRMLScene*)" signal in   is connected to
        #       each      MRML widget's   "setMRMLScene(vtkMRMLScene*)"     slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # 03. Create logic class. Logic implements all computations that should be possible to run
        #       in batch mode, without a graphical user interface.
        self.logic = sl__US_SeqViewerLogic()

        # 04. Connections, ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # 05. SL_Developer. Connect Signal-Slot,  ensure that whenever user changes some settings on the GUI,
        #                                         that is saved in the MRML scene (in the selected parameter node).
        self.ui.sequenceSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectedNodeChanged)
        slicer.modules.sequences.toolBar().activeBrowserNodeChanged.connect(self.onSelectedNodeChanged)

        self.ui.slider_SeqFrame.connect("valueChanged(int)", self.onSliderFrameIndex_ValueChanged)


        # 06. Needed for programmer-friendly  Module-Reload   where the Module had already been enter(self)-ed;
        #                                     Otherwise,      will initial through function     enter(self)
        if self.parent.isEntered:
            self.initializeParameterNode()  # Every-Module own a Singleton ParameterNode track by **Logic.moduleName!

    # ------------------------------------------------------------------------------------------------------------------
    def cleanup(self):
        """    Called when the application closes and the module widget is destroyed.    """
        print("**Widget.cleanup(self)")
        self.removeObservers()

    # ------------------------------------------------------------------------------------------------------------------
    def enter(self):
        """    Called each time the user opens this module.    """
        print("**Widget.enter(self)")

        # 01. Slicer.  SL__Note:   Every-Module own a Singleton ParameterNode that can be identified by
        #                                 self._parameterNode.GetAttribute('ModuleName')!  Need to initial every Entry!
        self.initializeParameterNode()

    # ------------------------------------------------------------------------------------------------------------------
    def exit(self):
        """    Called each time the user opens a different module.    """
        print("**Widget.exit(self)")
        # Slicer. Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # ------------------------------------------------------------------------------------------------------------------
    def onSceneStartClose(self, caller, event):
        """    Called just before the scene is closed.    """
        print("**Widget.onSceneStartClose(self, caller, event)")

        # Slicer. Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    # ------------------------------------------------------------------------------------------------------------------
    def onSceneEndClose(self, caller, event):
        """     Called just after the scene is closed.    """
        print("**Widget.onSceneEndClose(self, caller, event)")
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    # ------------------------------------------------------------------------------------------------------------------
    def initializeParameterNode(self):
        """    Ensure parameter node exists and observed. """
        # 01. Slicer-Initial: the Singleton ParameterNode stores all user choices in param-values, node selections...
        #         so that when the scene is saved and reloaded, these settings are restored.
        self.setParameterNode(self.logic.getParameterNode())

        # 02. SL_Developer. To update ParameterNode and attach observers
        pass


    # ------------------------------------------------------------------------------------------------------------------
    def setParameterNode(self, inputParameterNode):
        """    SL_Notes:  Set and observe the Singleton ParameterNode.
                  Observation is needed because when ParameterNode is changed then the GUI must be updated immediately.
        """
        print("**Widget.setParameterNode(self, inputParameterNode)")
        if inputParameterNode:
            if not inputParameterNode.IsSingleton():
                raise ValueError(f'SL__Allert! \tinputParameterNode = \n{inputParameterNode.__str__()}')
            self.logic.setDefaultParameters(inputParameterNode)

        # 01. Unobserve previously selected Singleton ParameterNode;
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 02. Set new Singleton ParameterNode and  Add an observer to the newly selected
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 03. Initial GUI update; need to do this GUI update whenever there is a change from the Singleton ParameterNode
        self.updateGUIFromParameterNode()

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section I:  get, set, obtain                ================================
    # ------------------------------------------------------------------------------------------------------------------
    def getSelectedItemNumber_FromGUI_Slider(self):
        # Slider FrameIndex starts from 1, but idx_SelectedItemNumber starts 0.
        idx_CurSeqBrowser_SelectedItemNumber = self.ui.slider_SeqFrame.value - INT_SliderFrameIndex_Min
        return idx_CurSeqBrowser_SelectedItemNumber

    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section II-A:  updateGUIFromParameterNode__  &    Slots   that call uiUpdate =
    # ------------------------------------------------------------------------------------------------------------------
    def updateGUIFromParameterNode(self, caller=None, event=None):
        """   This method is called whenever parameter node is changed.
              The module GUI is updated to show the current state of the parameter node.    """
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

        # 01. LogicUpdate
        self.updateParameterNodeFromGUI__Set_RefRoleNodeID(STR_SeqBrowserNode_RefRole_Selected, node_NewActiveBrowser.GetID())

        # 02. uiUpdate:     update  slider_SeqFrame
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
            #   II-02-D. Start uiUpdate
            self.uiUpdate_SwitchSelection_ChangeSeqBrowser_RemainFrameIndex(node_NewActiveBrowser)
            # --------------------------------------------------------------------------------------------------------------
            # III. Close-Brace: All the GUI updates are done;
            self._updatingGUIFromParameterNode = False

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # -----------        Section II-B:     Sub-Functions called by updateGUIFromParameterNode__  or Slot functions ---
    # ----- 1. All sub-functions starts with uiUpdate               ----------------------------------------------------
    # ----- 2. All uiUpdate functions                        canNOT     set     self._updatingGUIFromParameterNode  ----
    # ----- 3. The superior function who call uiUpdate function MUST    set     self._updatingGUIFromParameterNode  ----
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


    # ------------------------------------------------------------------------------------------------------------------
    def uiUpdate_PushSlicerScreenUpdate_by_ShakeTargetSeqBrowser(self, nodeTarget_SeqBrowser):
        print(f'  **Widget.uiUpdate_PushSlicerScreenUpdate_by_ShakeTargetSeqBrowser()')
        if nodeTarget_SeqBrowser:
            # Let's push Slicer to update by Setting current selected frame back and forth
            idx_curFrame = nodeTarget_SeqBrowser.GetSelectedItemNumber()

            nodeTarget_SeqBrowser.SetSelectedItemNumber(max(idx_curFrame - 1, 0))
            nodeTarget_SeqBrowser.SetSelectedItemNumber(min(idx_curFrame + 1, nodeTarget_SeqBrowser.GetNumberOfItems() - 1))
            nodeTarget_SeqBrowser.SetSelectedItemNumber(idx_curFrame)

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section IV:  updateParameterNodeFromGUI__       ==============================
    # ------------------------------------------------------------------------------------------------------------------
    def updateParameterNodeFromGUI__Set_RefRoleNodeID(self, STR_RefRole, str_NodeID):
        """   Read GUI Method:   Method updateParameterNodeFromGUI__ is called when users makes any change in the GUI.
              Changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
                    **Widget.updateParameterNodeFromGUI__Set_RefRoleNodeID(self, STR_RefRole, str_NodeID）    """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # I. Before  updating the Singleton ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        # II.   Update the Singleton ParameterNode; No updateGUIFromParameterNode triggered in this step
        node_BeforeChange = self._parameterNode.GetNodeReference(STR_RefRole)
        if node_BeforeChange:       str_NodeBeforeChange = self._parameterNode.GetNodeReference(STR_RefRole).GetID()
        else:                       str_NodeBeforeChange = "<class 'NoneType'>"
        print(f'\tBefore Update:  {str_NodeBeforeChange}')
        self._parameterNode.SetNodeReferenceID(STR_RefRole, str_NodeID)
        print(f'\tAfter Update:  {self._parameterNode.GetNodeReference(STR_RefRole).GetID()}')

        # III. After   updating the Singleton ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        self._parameterNode.EndModify(wasModified)


    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
''' ================================================================================================================='''
#
# sl__US_SeqViewerLogic
#
class sl__US_SeqViewerLogic(ScriptedLoadableModuleLogic):
    """   The Logic class is :  to facilitate dynamic reloading of the module without restarting the application.
          This class should implement all the actual computation done by your module.  
          The interface should be such that other python code can import this class 
                                        and make use of the functionality without requiring an instance of the Widget.
        Uses ScriptedLoadableModuleLogic base class, available at:
            https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """    Called when the logic class is instantiated. Can be used for initializing member variables.    """
        ScriptedLoadableModuleLogic.__init__(self)

        self._isSwitchingSeqBrowser = False

    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section VI:  get, set, obtain, & createNewNode          =====================
    # ------------------------------------------------------------------------------------------------------------------
    def obtain_idxSliderCurFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser):
        ''' **Logic.obtain_idxSliderCurFrame_from_TargetSeqBrowser(self, nodeTarget_SeqBrowser) ''' ''''''
        idx_SliderCurFrame = nodeTarget_SeqBrowser.GetSelectedItemNumber() + INT_SliderFrameIndex_Min
        return idx_SliderCurFrame


    # ------------------------------------------------------------------------------------------------------------------
    # ==================================================================================================================
    # ==================================================================================================================
    # ===========        SL_Developer,     Section VII-A:  logicUpdate     &    Functions   that call paramNodeUpdate ====
    # ------------------------------------------------------------------------------------------------------------------
    def setDefaultParameters(self, parameterNode):
        """    SL_Developer, B:    Initialize parameter node, Re-Enter, Re-Load.    """
        print("**Logic.setDefaultParameters(self, parameterNode), \tSL_Developer, B");
        # I. Before  updating the Singleton ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        wasModified = parameterNode.StartModify()  # Modify all properties in a single batch
        # --------------------------------------------------------------------------------------------------------------
        # II. Update the Singleton ParameterNode; No updateGUIFromParameterNode triggered in this step
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

        # --------------------------------------------------------------------------------------------------------------
        # III. After   updating the Singleton ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        parameterNode.EndModify(wasModified)


    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # -----------        Section VII-B:     Sub-Functions with prefix/surfix paramNodeUpdate      ----------------------
    # ----- 1. All sub-functions prefix/surfix with paramNodeUpdate;              --------------------------------------
    # ------2. All paramNodeUpdate functions                        canNOT     self.getParameterNode().StartModify() ---
    # ------3. The superior function who call paramNodeUpdate function MUST    self.getParameterNode().StartModify() ---
    # ------------------------------------------------------------------------------------------------------------------


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


    # ------------------------------------------------------------------------------------------------------------------
    # ---------------  Section VIII-02:     Set / Update      Functions          ---------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
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




''' ================================================================================================================='''
''' ================================================================================================================='''
''' ================================================================================================================='''
#
# sl__US_SeqViewerTest
#
class sl__US_SeqViewerTest(ScriptedLoadableModuleTest):
    """  This is the test case for your scripted module.
            Uses ScriptedLoadableModuleTest base class, available at:
                https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py  """
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.    """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.    """
        self.setUp()
        self.test_sl__US_SeqViewer1()

    def test_sl__US_SeqViewer1(self):
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


