import maya
maya.utils.loadStringResourcesForModule(__name__)

import zlib
import zipfile
import maya.cmds as cmds
from os import path

def pyError(errorString):
    """ print an error message """
    import maya.mel as mel
    try:
        mel.eval('error "%s"' % errorString)
    except: pass

def pyResult(resultString):
    """ print a result message """
    import maya.mel as mel
    msg = maya.stringTable['y_zipScene.kResult' ] % resultString
    mel.eval('print "%s"' % msg)

def zipScene(archiveUnloadedReferences):
    fileName = cmds.file(q=True, sceneName=True)
    # If the scene has not been saved
    if (fileName==""):
        pyError( maya.stringTable['y_zipScene.kSceneNotSavedError'  ] )
        return    

    # If the scene has been created, saved and then erased from the disk 
    elif (cmds.file(q=True, exists=True)==0):
        msg = maya.stringTable['y_zipScene.kNonexistentFileError' ] % fileName
        pyError(msg) 
        return
    
    # If the scene has been modified    
    elif (cmds.file(q=True, anyModified=True)==1):
                
                if(cmds.about(batch=True)):
                        # batch mode, save the scene automatically.
                        cmds.warning( maya.stringTable['y_zipScene.kSavingSceneBeforeArchiving' ] )
                        cmds.file(force=True, save=True)
                else:
                        noStr  = maya.stringTable['y_zipScene.kArchiveSceneNo'  ]
                        yesStr = maya.stringTable['y_zipScene.kArchiveSceneYes'  ]
                        dismissStr = 'dismiss'
                        result = cmds.confirmDialog( title=maya.stringTable['y_zipScene.kArchiveSceneTitle' ], message=maya.stringTable['y_zipScene.kArchiveSceneMsg' ], \
                                 button=[yesStr,noStr], defaultButton=yesStr, cancelButton=noStr, dismissString=dismissStr )
                        if(result == yesStr):
                              cmds.file(force=True, save=True)  
                        elif(result == dismissStr):                                
                           return   

    # get the default character encoding of the system
    theLocale = cmds.about(codeset=True)

    # get a list of all the files associated with the scene
    files = cmds.file(query=1, list=1, withoutCopyNumber=1)
    
    # create a zip file named the same as the scene by appending .zip to the name.
    # this need to be done before set(files) because set won't keep the order of filenames but we rely on that order to get the first one to construct zipFileName.
    zipFileName = (files[0])+'.zip'
    zip=zipfile.ZipFile(zipFileName, 'w', zipfile.ZIP_DEFLATED)
    
    # If user choose to archive unloaded reference files, then find all referenced files of the current scene. 
    # For any unloaded reference, load them first, get file list that should be archived and then restore its unloaded status.
    if( archiveUnloadedReferences == True):
        refNodes = cmds.ls(type='reference')
        isLoadOldList = []
        for refNode in refNodes:
            if(refNode.find('sharedReferenceNode') == -1):
                isLoadOld = cmds.referenceQuery(refNode, isLoaded=True)
                isLoadOldList.append(isLoadOld)
                # Load the unloaded reference
                if(isLoadOld == False):
                    cmds.file(loadReference=refNode, loadReferenceDepth = 'all')
                # Get all external files related to this reference
                filesOfThisRef = cmds.file(query=1, list=1, withoutCopyNumber=1)
                for fileOfThisRef in filesOfThisRef:
                    files.append(fileOfThisRef)
                # Unload the reference that are unloaded at the beginning
                if(isLoadOld == False):
                    cmds.file(unloadReference=refNode)    
        # remove the possible duplicated file names
        files = set(files)
        files = list(files)

    # add the project workspace.mel file also
    workspacePath = cmds.workspace(q = True, fullName = True) + '/workspace.mel'    
    files.append(workspacePath)
    
    # add each file associated with the scene, including the scene
    # to the .zip file
    for file in files:
        if(path.isfile(file)):
                        name = file.encode(theLocale)
                        zip.write(name)
        else:
                        msg = maya.stringTable['y_zipScene.kArchiveFileSkipped' ] % file
                        cmds.warning( msg )    
    zip.close()

    # output a message whose result is the name of the zip file newly created
    pyResult(zipFileName)
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
