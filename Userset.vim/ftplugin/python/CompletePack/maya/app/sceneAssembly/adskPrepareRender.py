"""
Prepare scene for rendering.
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)


import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import re

renderRepName = ''
renderRepType = ''
renderRepLabel = ''
useRegularExpression = False
adskPrepareRenderGlobalsNode = ''

def renderRepPredicate(aFnSet, aRepName):
    """
    Return true if the representation matches the criteria for name, label, and type. 
    If all criteria are empty, the representation does not match. 
    If one or more criteria are non-empty, those are used to determine the match.
    """
            
    if(renderRepName == '' and renderRepLabel == '' and renderRepType == ''):
        return False
    
    
    matchList=[(renderRepName, aRepName), \
               (renderRepLabel, aFnSet.getRepLabel(aRepName)), \
               (renderRepType, aFnSet.getRepType(aRepName))]
               
    matches = True
    
    for match in matchList:
        if match[0] != '' and matches:  
            matches = True if useRegularExpression and re.match(match[0], match[1]) else (match[0] == match[1])
                     
    return matches  
  
def activateRender(a):
    """
    Recursively activate the render representation on an assembly node.
    Return true if the representation matches criteria at least once. 
    """
    aFn = OpenMaya.MFnAssembly(a)

    # Get the list of representations.  If there's at least one representation
    # that matches the predicate, activate the first one to render it.
    # Otherwise, don't change the currently-active rep.
    representations = aFn.getRepresentations()
    
    matchingCriteria = False
    for r in representations:
        # Avoid activating a representation if it's currently active.        
        if renderRepPredicate(aFn, r):
            matchingCriteria = True
            if aFn.getActive() != r:
                aFn.activateNonRecursive(r)                
            break            
    
    # No matching criteria, un-activate the representation. 
    if not matchingCriteria:
        aFn.activateNonRecursive('')
        # Early out, no active representation.
        return False
    # Recurse down to nested assemblies, and activate their render
    # representation.
    subA = aFn.getSubAssemblies()
     
    for s in range(subA.length()):        
        if(activateRender(subA[s])):
            matchingCriteria = True
            
    return matchingCriteria

def preRender():
    """Prepare a scene for rendering by activating the render representation on all assembly nodes.
    """
    readFromGlobalsNode()
    
    # Go over all top-level assemblies, and traverse them to get them into 
    # rendering shape.
    topLevel = OpenMaya.MFnAssembly.getTopLevelAssemblies()
    
    matchingCriteria = False
    for a in range(topLevel.length()):
        if(activateRender(topLevel[a])):
            matchingCriteria = True
        
    if not matchingCriteria:
         cmds.warning( maya.stringTable['y_adskPrepareRender.kPrepareRenderNoMatchingCriteria' ] )
        
    return

def repNameChanged(repNameControl):
    """Callback invoked when the render settings UI control for the representation name regular expression text field changes.
    """
    global renderRepName
    global adskPrepareRenderGlobalsNode
    renderRepName = cmds.textFieldGrp(repNameControl, query=True, text=True)
    if len(adskPrepareRenderGlobalsNode) > 0:
        cmds.setAttr(adskPrepareRenderGlobalsNode + ".repName",renderRepName, type="string")

def repLabelChanged(repLabelControl):
    """Callback invoked when the render settings UI control for the representation label text field changes.
    """
    global renderRepLabel
    global adskPrepareRenderGlobalsNode
    renderRepLabel = cmds.textFieldGrp(repLabelControl, query=True, text=True)
    if len(adskPrepareRenderGlobalsNode) > 0:
        cmds.setAttr(adskPrepareRenderGlobalsNode + ".repLabel",renderRepLabel, type="string")

        
def repTypeChanged(repTypeControl):
    """Callback invoked when the render settings UI control for the representation type text field changes.
    """
    global renderRepType
    global adskPrepareRenderGlobalsNode
    renderRepType = cmds.textFieldGrp(repTypeControl, query=True, text=True)
    if len(adskPrepareRenderGlobalsNode) > 0:
        cmds.setAttr(adskPrepareRenderGlobalsNode + ".repType",renderRepType, type="string")

def useRegExChkBoxChanged(useRegExChkBoxControl):
    """Callback invoked when the render settings UI control for the representation check box to use regular expression changes.
    """
    global useRegularExpression
    global adskPrepareRenderGlobalsNode
    useRegularExpression = cmds.checkBoxGrp(useRegExChkBoxControl, query=True, v1=True)
    if len(adskPrepareRenderGlobalsNode) > 0:
        cmds.setAttr(adskPrepareRenderGlobalsNode + ".useRegExp",useRegularExpression)


def settingsUI():
    """Populate a parent form layout with UI controls for our traversal set.
    """
    
    readFromGlobalsNode()
    
    global renderRepName
    global renderRepLabel
    global renderRepType    
    global useRegularExpression    
    
    # Get our parent layout, which will be a form layout.
    traversalSetLayout = cmds.setParent(query=True)
   
    repName = cmds.textFieldGrp(ad2=2, label=maya.stringTable['y_adskPrepareRender.kSceneAssemblyRenderSettingRepName'], text=renderRepName)    
    repLabel = cmds.textFieldGrp(ad2=2, label=maya.stringTable['y_adskPrepareRender.kSceneAssemblyRenderSettingRepLabel'],text=renderRepLabel)
    repType = cmds.textFieldGrp(ad2=2, label=maya.stringTable['y_adskPrepareRender.kSceneAssemblyRenderSettingRepType'],text=renderRepType)
    useRegExp = cmds.checkBoxGrp(numberOfCheckBoxes=1, label=maya.stringTable['y_adskPrepareRender.kSceneAssemblyRenderSettingRgEx'], label1='', value1=useRegularExpression)
    cmds.textFieldGrp(repName, edit=True, changeCommand=('maya.app.sceneAssembly.adskPrepareRender.repNameChanged(\"' + repName + '\")'))    
    cmds.textFieldGrp(repLabel, edit=True, changeCommand=('maya.app.sceneAssembly.adskPrepareRender.repLabelChanged(\"' + repLabel + '\")'))
    cmds.textFieldGrp(repType, edit=True, changeCommand=('maya.app.sceneAssembly.adskPrepareRender.repTypeChanged(\"' + repType + '\")'))
    cmds.checkBoxGrp(useRegExp, edit=True, changeCommand=('maya.app.sceneAssembly.adskPrepareRender.useRegExChkBoxChanged(\"' + useRegExp + '\")'))

    cmds.formLayout(
        traversalSetLayout, edit=True,
        attachForm=[(repName,  'top',  0),
                    (repName,  'left', 0), (repName,  'right', 0),
                    (repLabel, 'left', 0), (repLabel, 'right', 0),
                    (repType,  'left', 0), (repType,  'right', 0),
                    (useRegExp, 'left', 135), (useRegExp, 'right', 0)],
        attachControl=[(repLabel,  'top', 0, repName),
                       (repType, 'top', 0, repLabel),
                       (useRegExp, 'top', 0, repType)])

    return

def readFromGlobalsNode():          
    global renderRepName
    global renderRepLabel
    global renderRepType  
    global useRegularExpression        
    global adskPrepareRenderGlobalsNode
           
    adskPrepareRenderGlobalsNode = cmds.ls(type="adskPrepareRenderGlobals") 
    if len(adskPrepareRenderGlobalsNode) > 0:
        adskPrepareRenderGlobalsNode = adskPrepareRenderGlobalsNode[0]
        renderRepName = cmds.getAttr(adskPrepareRenderGlobalsNode + ".repName")      
        renderRepLabel = cmds.getAttr(adskPrepareRenderGlobalsNode + ".repLabel")        
        renderRepType = cmds.getAttr(adskPrepareRenderGlobalsNode + ".repType")       
        useRegularExpression = cmds.getAttr(adskPrepareRenderGlobalsNode + ".useRegExp")
    else:
        adskPrepareRenderGlobalsNode = ''

# Ideally, we would create a default node (not saved in the scene file), and not implicitly created 
# (only set attribute changes are saved to file, not connections, which we don't need). Unfortunately, 
# default node creation from a command or the API is not possible. Furthermore, we should only be 
# creating this node when the default traversal set is changed to adskPrepareRender.
def createPrepareRenderGlobalsNode():    
    # Workaround for dirtying the scene until there's a way to create default
    # nodes through the API. This is hacky, but the safest thing to do for now.
    sceneDirty = cmds.file(query=True, modified=True) 
    
    cmds.createNode('adskPrepareRenderGlobals', shared=True, skipSelect=True, name='adskPrepareRenderGlobals')
    
    # if the scene was previously unmodified, return it to that state since
    # we've only created a shared node which are only holding attributes
    # in their default state.
    if not (sceneDirty):
        cmds.file(modified=False)  

    return


# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
