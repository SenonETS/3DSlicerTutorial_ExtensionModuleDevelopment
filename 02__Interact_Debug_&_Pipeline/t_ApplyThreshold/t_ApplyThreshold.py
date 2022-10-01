import logging
import os

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

'''=================================================================================================================='''
'''=================================================================================================================='''
#
# t_ApplyThreshold
#
class t_ApplyThreshold(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "t_ApplyThreshold"
        self.parent.categories = ["SL_Tutorials"]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Sen Li (École de Technologie Supérieure)"]
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """This is t_ApplyThreshold ! """
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)

        print("t_ApplyThreshold(ScriptedLoadableModule):    __init__(self, parent)")

'''=================================================================================================================='''
'''=================================================================================================================='''
#
# t_ApplyThresholdWidget
#
class t_ApplyThresholdWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

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
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/t_ApplyThreshold.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # 02. Set scene in MRML widgets. Make sure that in Qt designer the
        #       top-level qMRMLWidget's   "mrmlSceneChanged(vtkMRMLScene*)" signal in   is connected to
        #       each      MRML widget's   "setMRMLScene(vtkMRMLScene*)"     slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # 03. Create logic class. Logic implements all computations that should be possible to run
        #       in batch mode, without a graphical user interface.
        self.logic = t_ApplyThresholdLogic()

        # 04. Connections, ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # 05. SL_Developer. Connect Signal-Slot,  ensure that whenever user changes some settings on the GUI,
        #                                         that is saved in the MRML scene (in the selected parameter node).
        self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)

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

        # 02. SL_Developer. Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

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
        #       II-01. Update node selectors and sliders
        self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
        self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
        self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")
        #       II-02. Update buttons states and tooltips
        if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
            self.ui.applyButton.toolTip = "Compute output volume"
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = "Select input and output volume nodes"
            self.ui.applyButton.enabled = False
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

        # II.   Update the SingleTon ParameterNode; No updateGUIFromParameterNode triggered in this step
        self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
        self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
        self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        # III. After   updating the SingleTon ParameterNode; Enable Modify events, e.g., vtk.vtkCommand.ModifiedEvent
        self._parameterNode.EndModify(wasModified)

    # ------------------------------------------------------------------------------------------------------------------
    def onApplyButton(self):
        """ SL_Developer. Run processing when user clicks "Apply" button.     """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


'''=================================================================================================================='''
'''=================================================================================================================='''
#
# t_ApplyThresholdLogic
#
class t_ApplyThresholdLogic(ScriptedLoadableModuleLogic):
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

        """        Initialize parameter node with default settings.       """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    # ------------------------------------------------------------------------------------------------------------------
    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')

''' ================================================================================================================='''
''' ================================================================================================================='''
#
# t_ApplyThresholdTest
#
class t_ApplyThresholdTest(ScriptedLoadableModuleTest):
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
        self.test_t_ApplyThreshold1()

    # ------------------------------------------------------------------------------------------------------------------
    def test_t_ApplyThreshold1(self):
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

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('t_ApplyThreshold1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = t_ApplyThresholdLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')

# ======================================================================================================================
# ======================================================================================================================
# ------------     Unit-Test:   Load Data        -----------------------------------------------------------------------

#
# Register sample data sets in Sample Data module
#
def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # t_ApplyThreshold1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='t_ApplyThreshold',
        sampleName='t_ApplyThreshold1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 't_ApplyThreshold1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='t_ApplyThreshold1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='t_ApplyThreshold1'
    )

    # t_ApplyThreshold2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='t_ApplyThreshold',
        sampleName='t_ApplyThreshold2',
        thumbnailFileName=os.path.join(iconsPath, 't_ApplyThreshold2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='t_ApplyThreshold2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='t_ApplyThreshold2'
    )

