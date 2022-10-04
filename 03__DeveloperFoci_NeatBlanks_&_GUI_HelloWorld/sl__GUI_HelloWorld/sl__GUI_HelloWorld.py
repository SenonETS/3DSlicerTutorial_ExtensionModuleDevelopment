import logging
import os

import vtk

import slicer, qt
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

'''=================================================================================================================='''
'''=================================================================================================================='''
#
# sl__GUI_HelloWorld
#
class sl__GUI_HelloWorld(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "sl__GUI_HelloWorld"
        self.parent.categories = ["SL_Tutorials"]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Sen Li (École de Technologie Supérieure)"]
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """This is sl__GUI_HelloWorld ! """
        self.parent.acknowledgementText = 'Step-by-step tutorial on 3D Slicer extension development. ' \
                                          '\nThis file was originally developed by Sen Li, LATIS, École de techonologie supérieure. ' \
                                          '\nSen.Li.1@ens.etsmtl.ca'

        print("sl__GUI_HelloWorld(ScriptedLoadableModule):    __init__(self, parent)")

'''=================================================================================================================='''
'''=================================================================================================================='''
#
# sl__GUI_HelloWorldWidget
#
class sl__GUI_HelloWorldWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

    def __init__(self, parent=None):
        """    Called when the user opens the module the first time and the widget is initialized.    """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None # SingleTon initialized through self.setParameterNode(self.logic.getParameterNode())
        self._updatingGUIFromParameterNode = False
        print("**Widget.__init__(self, parent)")

    # ------------------------------------------------------------------------------------------------------------------
    def setup(self):
        print("**Widget.setup(self), \tSL_Developer")

        """    00. Called when the user opens the module the first time and the widget is initialized. """
        ScriptedLoadableModuleWidget.setup(self)

        # 01. Load widget from .ui file (created by Qt Designer).
        #       Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/sl__GUI_HelloWorld.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # 02. Set scene in MRML widgets. Make sure that in Qt designer the
        #       top-level qMRMLWidget's   "mrmlSceneChanged(vtkMRMLScene*)" signal in   is connected to
        #       each      MRML widget's   "setMRMLScene(vtkMRMLScene*)"     slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # 03. Create logic class. Logic implements all computations that should be possible to run
        #       in batch mode, without a graphical user interface.
        self.logic = sl__GUI_HelloWorldLogic()

        # 04. Connections, ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # 05. SL_Developer. Connect Signal-Slot,  ensure that whenever user changes some settings on the GUI,
        #                                         that is saved in the MRML scene (in the selected parameter node).
        self.ui.pushButton_HelloWorld.clicked.connect(self.onButtonHelloWorld_Clicked)

        # 06. Needed for programmer-friendly  Module-Reload   where the Module had already been enter(self)-ed;
        #                                     Otherwise,      will initial through function     enter(self)
        if self.parent.isEntered:
            self.initializeParameterNode()

    # ------------------------------------------------------------------------------------------------------------------
    def cleanup(self):
        """    Called when the application closes and the module widget is destroyed.    """
        print("**Widget.cleanup(self)")
        self.removeObservers()

    # ------------------------------------------------------------------------------------------------------------------
    def enter(self):
        """    Called each time the user opens this module.    """
        print("\n**Widget.enter(self)")

        # 01. Slicer.   SL__Note:   Every-Module own a SingleTon ParameterNode that can be identified by
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
        """     Called just after the scene is closed.    """''''''
        print("**Widget.onSceneEndClose(self, caller, event)")
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    # ------------------------------------------------------------------------------------------------------------------
    def initializeParameterNode(self):
        """    Ensure parameter node exists and observed. """''''''
        print("\t**Widget.initializeParameterNode(self), \t SL_Developer")
        # 01. Slicer-Initial: the SingleTon ParameterNode stores all user choices in param-values, node selections...
        #         so that when the scene is saved and reloaded, these settings are restored.
        self.setParameterNode(self.logic.getParameterNode())

        # 02. SL_Developer. To update ParameterNode and attach observers
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def setParameterNode(self, inputParameterNode):
        """    SL_Notes:  Set and observe the SingleTon ParameterNode.
                  Observation is needed because when ParameteNode is changed then the GUI must be updated immediately.
        """
        print("\t\t**Widget.setParameterNode(self, inputParameterNode)")
        if inputParameterNode:
            if not inputParameterNode.IsSingleton():
                raise ValueError(f'SL__Allert! \tinputParameterNode = \n{inputParameterNode.__str__()}')
            self.logic.setDefaultParameters(inputParameterNode)

        # 01. Unobserve previously selected SingleTon ParameterNode
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 02. Set new SingleTon ParameterNode and  Add an observer to the newly selected -> immediate GUI reflection
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        # 03. Initial GUI update; need to do this GUI update whenever there is a change from the SingleTon ParameterNode
        self.updateGUIFromParameterNode()

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
        # II. SL_Developer.  In-Brace,   Update UI widgets ()
        print("**Widget.updateGUIFromParameterNode(self, caller=None, event=None), \tSL_Developer")
        #       II-01. Update buttons states and tooltips
        self.ui.pushButton_HelloWorld.toolTip = "Click Me and join SL Slicer Tutorial World"
        self.ui.pushButton_HelloWorld.enabled = True
        # --------------------------------------------------------------------------------------------------------------
        # III. Close-Brace: All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """ Read GUI Method:   Method updateParameterNodeFromGUI__ is called when users makes any change in the GUI.
              Changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """
        print(f"**Widget.updateParameterNodeFromGUI(self, caller=None, event=None),     \t SL_Developer")
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # I. Before  updating the SingleTon ParameterNode; Disable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        # II.   SL_Developer. Update the Singleton ParameterNode; No updateGUIFromParameterNode triggered in this step
        # self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)

        # III. After   updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        self._parameterNode.EndModify(wasModified)

    # ------------------------------------------------------------------------------------------------------------------
    def onButtonHelloWorld_Clicked(self):
        """ SL_Developer. Run processing when user clicks "Hello World" button.     """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            str_Result = self.logic.obtainStr_HelloWorld()
            qt.QMessageBox.information(slicer.util.mainWindow(), 'SL Tutorial: GUI HelloWorld', str_Result)


'''=================================================================================================================='''
'''=================================================================================================================='''
#
# sl__GUI_HelloWorldLogic
#
class sl__GUI_HelloWorldLogic(ScriptedLoadableModuleLogic):
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
        print("**Logic.__init__(self)")

    # ------------------------------------------------------------------------------------------------------------------
    def setDefaultParameters(self, parameterNode):
        """    SL_Developer:    Initialize parameter node, Re-Enter, Re-Load.    """''''''
        print("\t\t\t**Logic.setDefaultParameters(self, parameterNode), \tSL_Developer");

        # To initial ModuleSingleton ParameterNode
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def obtainStr_HelloWorld(self):
        """ To be called without GUI **Widget. """
        return "SL: Hello World!"














''' ================================================================================================================='''
''' ================================================================================================================='''
''' ================================================================================================================='''
#
# sl__GUI_HelloWorldTest
#
class sl__GUI_HelloWorldTest(ScriptedLoadableModuleTest):
    """  This is the test case for your scripted module.
            Uses ScriptedLoadableModuleTest base class, available at:
                https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.    """
        slicer.mrmlScene.Clear()

    # ------------------------------------------------------------------------------------------------------------------
    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_sl__GUI_HelloWorld1()

    # ------------------------------------------------------------------------------------------------------------------
    def test_sl__GUI_HelloWorld1(self):
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

        # Test the module logic
        logic = sl__GUI_HelloWorldLogic()
        str_Result = logic.obtainStr_HelloWorld()
        self.assertIsNotNone(str_Result)
        self.delayDisplay('Test passed')
