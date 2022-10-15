cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerIGSpineDeformity)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/SenonETS/3DSlicerTutorial_ExtensionModuleDevelopment")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Sen Li (École de technologie supérieure)")
set(EXTENSION_DESCRIPTION "Spine deformity analysis using freehand 3D ultrasound.")
set(EXTENSION_ICONURL "https://github.com/SenonETS/3DSlicerTutorial_ExtensionModuleDevelopment/blob/master/sl_01__LaminaLandmark_Labeling/Resources/Icons/SlicerIGSpineDeformity.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/SenonETS/3DSlicerTutorial_ExtensionModuleDevelopment/blob/master/sl_01__LaminaLandmark_Labeling/SL_ScreenShot.PNG")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(sl_01__LaminaLandmark_Labeling)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
