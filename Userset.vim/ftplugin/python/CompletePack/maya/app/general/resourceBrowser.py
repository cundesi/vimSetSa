"""
This class creates and manages the resource browser
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)

import maya.cmds as cmds
import maya.mel as mel
import os.path
from functools import partial

class resourceBrowser:
  # ---------------------------------------------------------------------------
  def __init__(self):
    self.winName = "resourcesBrowser"
    self.verbose = False
    self.currentResource = None

  # ---------------------------------------------------------------------------
  def info(self, msg):
    'Print msg if verbose mode is on'
    if self.verbose:
      print ("INFO (%s): " % self.__class__.__name__)+msg

  # ---------------------------------------------------------------------------
  def currentResourceName(self):
    'Return the current resource name or None'
    self.info('currentResource()')
    selIndx = cmds.textScrollList(self.wList, query=True,
                                  selectIndexedItem=True)
    if (selIndx is None) or (len(selIndx) < 1):
      return None
    return self.resList[selIndx[0]-1]

  # ---------------------------------------------------------------------------
  def updatePreview(self):
    'Select a new icon'
    self.info('updatePreview()')
    
    self.currentResource = self.currentResourceName()
    imageName = self.currentResource
    selected = True
    if imageName is None:
      imageName = "commandButton.png"
      selected = False

    cmds.iconTextStaticLabel(self.wItemImage, edit=True,
                     image=imageName, enable=selected)

  # ---------------------------------------------------------------------------
  def updateFilter(self, data):
    "Update the list based on the new filter"
    self.info('updateFilter')
    filterVal = cmds.textFieldGrp(self.wFilter, query=True, text=True)
    self.resList = cmds.resourceManager(nameFilter=filterVal+'*')
    if self.resList is None:
      self.resList = []

    # Populate the list with all icons from the resources
    cmds.textScrollList(self.wList, edit=True, removeAll=True)
    for name in self.resList:
      cmds.textScrollList(self.wList, edit=True, append=name)
    cmds.textScrollList(self.wList, edit=True, selectIndexedItem=1)
    self.updatePreview()
    cmds.setFocus(self.wList)

  # ---------------------------------------------------------------------------
  def saveCopy(self, data):
    "Button callback to end the dialog"
    self.info('saveCopy')

    resName = self.currentResourceName()
    if resName is None:
      return

    ext = os.path.splitext(resName)[1]
    if ext == '':
      ext = '.png'

    # Bring a file browser to select where to save the copy
    captionStr = maya.stringTable['y_resourceBrowser.kPickIconCaption' ];
    iconDir = cmds.internalVar( userBitmapsDir=True)
    fileList = cmds.fileDialog2(caption=captionStr,
                                fileMode=0,
                                okCaption=captionStr,
                                fileFilter='*'+ext,
                                startingDirectory=iconDir)
    path = None
    if fileList is not None:
      if (len(fileList) > 0) and (fileList[0] <> ""):
        path = fileList[0]

    if path is not None:
      self.info("saveCopy: Path="+path)
      cmds.resourceManager(saveAs=(resName, path))
      
  # ---------------------------------------------------------------------------
  def buttonCallback(self, data, dismissMsg=''):
    "Button callback to end the dialog"
    cmds.layoutDialog(dismiss=dismissMsg)

  # ---------------------------------------------------------------------------
  def populateUI(self):
    "Create the resource browser window UI"

    # Get the dialog's formLayout.
    #
    form = cmds.setParent(q=True)

    self.wItemImage = cmds.iconTextStaticLabel(image="commandButton.png")
    self.wFilter = cmds.textFieldGrp(label=maya.stringTable['y_resourceBrowser.kFilter' ],
                               columnAttach=[(1, "right", 5), (2, "both", 0)],
                               columnWidth=(1, 75),
                               text='',
                               changeCommand=self.updateFilter)
    self.wList = cmds.textScrollList(numberOfRows=11,
                                     allowMultiSelection=False,
                                     selectCommand=self.updatePreview)
    b1 = cmds.button(label=maya.stringTable['y_resourceBrowser.kSelect' ],
                     command=partial(self.buttonCallback, dismissMsg="valid"))
    b2 = cmds.button(label=maya.stringTable['y_resourceBrowser.kSaveCopy' ],
                     annotation=maya.stringTable['y_resourceBrowser.kSaveCopyAnn' ],
                     command=self.saveCopy)
    b3 = cmds.button(label=maya.stringTable['y_resourceBrowser.kCancel' ],
                     command=self.buttonCallback)

    cmds.formLayout(form, edit=True,
					attachForm=[(self.wItemImage, 'top', 6),
                                (self.wItemImage, 'left', 6),
                                (self.wItemImage, 'right', 6),

                                (self.wFilter, 'left', 6),
                                (self.wFilter, 'right', 6),

                                (self.wList, 'left', 6),
                                (self.wList, 'right', 6),

                                (b1, 'left', 6),
                                (b1, 'bottom', 6),
                                (b2, 'bottom', 6),
                                (b3, 'right', 6),
                                (b3, 'bottom', 6)],

                    attachPosition=[(b1, 'right', 3, 33),
                                    (b2, 'right', 3, 66)],

					attachControl=[(self.wFilter, 'top', 6, self.wItemImage),
                                   (self.wList, 'top', 6, self.wFilter),
                                   (self.wList, 'bottom', 6, b1),

                                   (b2, 'left', 6, b1),
                                   (b3, 'left', 6, b2)
                                   ]
                    )

    self.updateFilter('')

  # ---------------------------------------------------------------------------
  def run(self):
    """Display the Factory Icon Browser window. Return the selected
    resource or None
    """

    result = cmds.layoutDialog(title = maya.stringTable['y_resourceBrowser.kShelves' ],
                               ui=self.populateUI)
    self.info('result = %s' % result)

    if result == 'valid':
      return self.currentResource
    return None
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
