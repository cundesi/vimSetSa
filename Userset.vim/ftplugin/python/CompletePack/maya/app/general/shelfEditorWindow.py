"""
This class creates and manages the shelf editor window
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)

import maya.utils as utils
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import maya.app.general.resourceBrowser as resourceBrowser

# ---------------------------------------------------------------------------
def doIt(windowName="shelfEditor",selectedShelfButton=None, selectedTabIndex=2):
  "Main function to create a shelfEditorWindow object and run it"
  thisWindow = shelfEditorWindow(windowName=windowName)
  thisWindow.create(selectedShelfButton, selectedTabIndex)

class shelfEditorWindow:
  # ---------------------------------------------------------------------------
  def __init__(self, windowName="shelfEditor"):
    self.winName = windowName
    self.verbose = False
    self.col1width = 200
    self.defaultRGB = (.8, .8, .8)

    # Shared I18N messages
    self.moveUpStr   = maya.stringTable[ 'y_shelfEditorWindow.kMoveUp'  ]
    self.moveDownStr = maya.stringTable[ 'y_shelfEditorWindow.kMoveDown'  ]

    self.mainShelfLayout = mel.eval('global string $gShelfTopLevel; string $tmp=$gShelfTopLevel;')
    # This is needed for shelfLabel_uiToMel / shelfLabel_melToUI
    mel.eval('if(! `exists shelfLabel_uiToMel` ) {source "shelfLabel.mel";}')

  # ---------------------------------------------------------------------------
  def info(self, msg):
    'Print msg if verbose mode is on'
    if self.verbose:
      print ("INFO (%s): " % self.__class__.__name__)+msg

  # ---------------------------------------------------------------------------
  def selectedIndex(self, list):
    'Return the 1-based index of the selected item in the list or None'
    indx = cmds.textScrollList(list, query=True, selectIndexedItem=True)
    if indx is None or (len(indx) < 1):
      return None
    return indx[0]

  # ---------------------------------------------------------------------------
  def uiLabel(self, key):
    'Return the I18N version of the shelf name'
    return mel.eval('shelfLabel_melToUI("%s")' % key)

  # ---------------------------------------------------------------------------
  def internalName(self, name):
    'Return the internal shelf name for a given I18N name'
    return mel.eval('shelfLabel_uiToMel("%s")' % name)

  def fromNativePath(self, strFile):
    if cmds.about(nt=True):
      strFile = strFile.replace('\\','/')
    return strFile

  # ---------------------------------------------------------------------------
  def setStyle(self, style, data):
    """Menu callback to set the style of the shelf items. Known styles
    are 'iconOnly', 'iconAndTextVertical', 'iconAndTextHorizontal'
    """
    self.info('setStyle style=%s, data=%s' % (style, data))
    mel.eval('setShelfStyle("%s", "Small")' % style)
    cmds.optionVar(stringValue=('shelfItemStyle', style))

  # ---------------------------------------------------------------------------
  def setSaveMode(self, mode, data):
    """Menu callback to set the save mode for the shelves
    """
    self.info('setSaveMode mode=%d, data=%s' % (mode, data))
    cmds.optionVar(intValue=('isShelfSave', mode))

  # ---------------------------------------------------------------------------
  def getAlignment(self, indx):
    if cmds.optionVar(ex='shelfAlign'+str(indx)):
      return cmds.optionVar(query='shelfAlign'+str(indx))
    return 'left'

  # ---------------------------------------------------------------------------
  def moveShelf(self, direction, data):
    'Move the current shelf up or down one level'
    self.info('moveShelf direction=%d' % direction)

    shelfLayout = self.mainShelfLayout

    numShelves = cmds.tabLayout(shelfLayout, query=True, numberOfChildren=True)
    indx = self.selectedIndex(self.wShelfList)
    if indx is None:
      return

    newIndx = indx + direction
    if (newIndx < 1) or (newIndx > numShelves):
      return

    # Move the shelf
    cmds.tabLayout(shelfLayout, edit=True, moveTab=(indx, newIndx))

    # Swap the optionVars
    # FIXME: can we remove this?
    load = cmds.optionVar(query='shelfLoad'+str(indx))
    name = cmds.optionVar(query='shelfName'+str(indx))
    file = cmds.optionVar(query='shelfFile'+str(indx))
    align = self.getAlignment(indx)
    newLoad = cmds.optionVar(query='shelfLoad'+str(newIndx))
    newName = cmds.optionVar(query='shelfName'+str(newIndx))
    newFile = cmds.optionVar(query='shelfFile'+str(newIndx))
    newAlign = self.getAlignment(newIndx)

    cmds.optionVar(intValue=('shelfLoad'+str(indx), newLoad),
                   stringValue=(('shelfName'+str(indx), newName),
                                ('shelfFile'+str(indx), newFile),
								('shelfAlign'+str(indx), newAlign))
                   )
    cmds.optionVar(intValue=('shelfLoad'+str(newIndx), load),
                   stringValue=(('shelfName'+str(newIndx), name),
                                ('shelfFile'+str(newIndx), file),
								('shelfAlign'+str(newIndx), align))
                   )

    self.updateShelfList(at=newIndx)

  # ---------------------------------------------------------------------------
  def newShelf(self, data):
    'Create a new shelf'
    self.info('newShelf data=%s' % data)

    indx = self.selectedIndex(self.wShelfList)
    mel.eval('addNewShelfTab "";')
    # Index to the newly created shelf
    last = cmds.tabLayout(self.mainShelfLayout, query=True, numberOfChildren=True)
    self.updateShelfList(at=last)
    if indx is not None:
      # If a shelf was selected, move the new one just after
      self.moveShelf(indx-last+1, '')

  # ---------------------------------------------------------------------------
  def deleteShelf(self, data):
    'Delete the current shelf'
    self.info('deleteShelf data=%s' % data)

    shelf = self.currentShelf(short=True)
    index = self.selectedIndex(self.wShelfList)
    if shelf is None or index is None:
      return
    if index > 1:
      # We'll move to the previous shelf in the list if possible. Note 
      # that indexes are 1-based
      index = index - 1

    if mel.eval('deleteShelfTab "%s"' % shelf):
      self.updateShelfList(at=index)

  # ---------------------------------------------------------------------------
  def selectShelf(self):
    'Select a new shelf'
    self.info('selectShelf')
    # Switch Maya UI to the shelf just selected
    shelfIndx = self.selectedIndex(self.wShelfList)
    if shelfIndx == None:
      return
    cmds.tabLayout(self.mainShelfLayout, edit=True, selectTabIndex=shelfIndx)

    currShelf = self.currentShelfName()
    cmds.textFieldGrp(self.wShelfName, edit=True, text=currShelf)
    currShelf = self.currentShelf()
    if not currShelf is None:
		align = cmds.shelfLayout(currShelf, q=True, aln=True)
		align = [1,2][align=='right']
		cmds.optionMenuGrp(self.wShelfAlign, edit=True, select=align)
    self.updateItemList()

  # ---------------------------------------------------------------------------
  def nbItems(self):
    'return the number of items in the current shelf'
    currShelf = self.currentShelf()
    if currShelf is None:
      return 0
    items = cmds.shelfLayout(currShelf, query=True, childArray=True)
    if items is not None:
      return len(items)
    return 0

  # ---------------------------------------------------------------------------
  def moveItem(self, direction, data):
    'Move the current item up or down one level'
    self.info('moveItem direction=%d, data=%s' % (direction, data))

    currShelf = self.currentShelf()
    if currShelf is None:
      return
    indx = self.selectedIndex(self.wItemList)
    if indx is None:
      return

    numItems = self.nbItems()
    if numItems == 0:
      return
    newIndx = indx + direction
    if (newIndx < 1) or (newIndx > numItems):
      return

    # Move the item
    self.info('\tShelf %s: moving %s from %d to %d' %
              (currShelf, self.currentItem(short=True), indx, newIndx))
    cmds.shelfLayout(currShelf, edit=True,
                     position=(self.currentItem(short=True), newIndx))
    self.updateItemList(at=newIndx)

  # ---------------------------------------------------------------------------
  def newItem(self, data):
    'Create a new item'
    self.info('newItem data=%s' % data)

    currShelf = self.currentShelf()
    if currShelf is None:
      return

    indx = self.selectedIndex(self.wItemList)
    newItem = cmds.shelfButton(parent=currShelf,
                               label="User Script", image="commandButton.png",
                               command='print("User defined macro");',
                               sourceType='MEL',
                               style=cmds.optionVar(q='shelfItemStyle'))

    if indx is not None:
      indx = indx+1
      self.info('\tNew icon at position %d' % indx)
      cmds.shelfLayout(currShelf, edit=True,
                       position=(newItem, indx))
    else:
      indx = self.nbItems()

    self.updateItemList(at=indx)
    self.updateItemData()

  # ---------------------------------------------------------------------------
  def deleteItem(self, data):
    'Delete the current item'
    self.info('deleteItem data=%s' % data)

    currItem = self.currentItem()
    index = self.selectedIndex(self.wItemList)
    if currItem is None or index is None:
      return
    if cmds.toolButton(currItem, exists=True ):
      # For tool buttons, we need to delete all the contexts
      #
      contexts = cmds.toolButton(currItem, query=True, toolArray=True)
      for context in contexts:
        cmds.deleteUI( context, toolContext=True )
    cmds.deleteUI(currItem)

    if index > self.nbItems():
      index = index - 1
    self.info('\tdeleteItem: index is %d' % index)

    self.updateItemList(at=index)
    self.updateItemData()

  # ---------------------------------------------------------------------------
  def selectItem(self):
    'Selects a new item'
    self.info('selectItem')
    currItem = self.currentItemName()
    # Name field editing is only allowed for shelfButton (not for toolButton)
    #
    cmds.textFieldGrp(self.wItemName, edit=True, text=currItem, enable=cmds.shelfButton( self.currentItem(), exists=True ))
    self.updateItemData()

  # ---------------------------------------------------------------------------
  def shelfName(self, data):
    'Rename the current shelf'
    self.info('shelfName data=%s' % data)

    currShelf = self.currentShelf()
    if currShelf is None:
      return
    name = cmds.textFieldGrp(self.wShelfName, query=True, text=True)
    if name == self.currentShelfName():
      # This callback can be called even if the name did not actually
      # changed. validateShelfName will not handle that case
      # gracefully.
      return

    # Save the current shelf name to remove the file later on
    oldShelfName = self.internalName(self.currentShelfName())

    self.info('\tRenaming "%s" to "%s"' %(currShelf, name))
    # Only accept valid shelf names
    self.info('\tvalidateShelfName("%s")' % name)
    if not mel.eval('validateShelfName("%s")' % name.replace('\\', '\\\\')):
      name = self.currentShelfName()
      cmds.textFieldGrp(self.wShelfName, edit=True, text=name)
      return

    # Update prefs
    sel = cmds.textScrollList(self.wShelfList, query=True,
                              selectIndexedItem=True)
    cmds.optionVar(stringValue=(('shelfName'+str(sel[0]), name),
                                ('shelfFile'+str(sel[0]), 'shelf_'+name))
                   )

    # Rename the shelfLayout
    cmds.renameUI(currShelf, name)

    # Rename the tab and textScrollList item
    cmds.tabLayout(self.mainShelfLayout, edit=True, tabLabel=(name, self.uiLabel(name)))
    self.updateShelfList(at=sel)

    # Rename the file
    shelfDirs = cmds.internalVar(userShelfDir=True)
    sep = None
    if cmds.about(win=True):
      sep = ';'
    else:
      sep = ':'
    shelfArray = shelfDirs.split(sep)
    for shelf in shelfArray:
      oldFileName = shelf+'shelf_'+oldShelfName+'.mel'
      if cmds.file(oldFileName, query=True, exists=True):
        cmds.saveShelf(name, (shelf+'shelf_'+name))
        cmds.sysFile(oldFileName, delete=True)
        break

  # ---------------------------------------------------------------------------
  def shelfAlignment(self, data):
    'Change the current shelfs alignment'
    self.info('shelfAlignment data=%s' % data)

    currShelf = self.currentShelf()
    if currShelf is None:
      return

    align = cmds.optionMenuGrp(self.wShelfAlign, q=True, select=True)
    align = ['left','right'][align==2]
    cmds.shelfLayout(currShelf, e=True, aln=align)

    # Update prefs
    sel = cmds.textScrollList(self.wShelfList, query=True,
                              selectIndexedItem=True)
    cmds.optionVar(stringValue=(('shelfAlign'+str(sel[0]), align)))
	
  # ---------------------------------------------------------------------------
  def itemIcon(self, internalIcon, data):
    'Change the current icon'
    self.info('itemIcon internalIcon=%s, data=%s' %(str(internalIcon), data))

    currItem = self.currentItem()
    if currItem is None:
      return

    path = None
    if internalIcon:
      resBrowser = resourceBrowser.resourceBrowser()
      path = resBrowser.run()
      del resBrowser
    else:
      # Bring a file browser to select the icon
      openStr = maya.stringTable['y_shelfEditorWindow.kPickIconCaption' ]
      filters = mel.eval('buildPixmapFileFilterList()')
      iconDir = cmds.internalVar( userBitmapsDir=True)
      fileList = cmds.fileDialog2(caption=openStr,
                                  fileMode=1,
                                  okCaption=openStr,
                                  fileFilter=filters,
                                  startingDirectory=iconDir)
      if fileList is not None:
        if (len(fileList) > 0) and (fileList[0] <> ""):
          path = self.fromNativePath(fileList[0])

    if path is not None:
      self.info("\titemIcon: Path="+path)
      if cmds.toolButton(currItem, exists=True ):
        # We have a tool button, not a shelf button; update image1 instead
        #
        cmds.toolButton(currItem, edit=True, image1=path)
      else:
        cmds.shelfButton(currItem, edit=True, image=path)
      self.updateItemData()

  # ---------------------------------------------------------------------------
  def itemName(self, data):
    'Rename the current item'
    self.info('itemName data=%s' % data)
    name = cmds.textFieldGrp(self.wItemName, query=True, text=True)
    currItem = self.currentItem()
    if currItem is None:
      return
    currIndx = self.selectedIndex(self.wItemList)
    if cmds.shelfButton(currItem, exists=True ):
      # We have a shelf button, go ahead and update the name; we don't handle
      # name changes for toolButtons yet (and never did, even prior to QT)
      #
      cmds.shelfButton(currItem, edit=True, label=name)
    self.updateItemList(at=currIndx)

  # ---------------------------------------------------------------------------
  def itemData(self, data):
    'Change the current item data'
    self.info('itemData data=%s' % data)

    currItem = self.currentItem()
    if currItem is None:
      return

    image =          cmds.iconTextStaticLabel(self.wItemImage, query=True, image=True)
    annotation =     cmds.textFieldGrp(self.wItemTip, query=True, text=True)
    label =          cmds.textFieldGrp(self.wItemLabel, query=True, text=True)
    labelColor =     cmds.colorSliderGrp(self.wItemLabelColor,
                                         query=True, rgbValue=True)
    labelBackColor = cmds.colorSliderGrp(self.wItemLabelBckColor, query=True,
                                         rgbValue=True)
    labelBackColor.append(cmds.floatSliderGrp(self.wItemLabelBckTransp,
                                              query=True, value=True))
    customBackColor = cmds.checkBoxGrp(self.wItemUserColor,
                                       query=True, value1=True)
    itemBackColor = cmds.colorSliderGrp(self.wItemBckColor, query=True,
                                        rgbValue=True)
    cmds.colorSliderGrp(self.wItemBckColor, edit=True, enable=customBackColor)

    lang = "mel"
    if cmds.radioButtonGrp(self.wLanguage, query=True, select=True) == 2:
      lang = "python"
    langDbl = "mel"
    if cmds.radioButtonGrp(self.wLanguageDbl, query=True, select=True) == 2:
      langDbl = "python"

    self.info("\titemData: update item %s (%s/%s)" % (currItem, lang, langDbl))

    if cmds.toolButton(currItem, exists=True ):
      # Tool buttons have to be handled differently; they have very few things
      # that can be modified (basically, just the image)
      #
      cmds.toolButton(currItem, edit=True,
                       image1=image)
      # Update the item preview:
      cmds.iconTextStaticLabel(self.wItemImage, edit=True,
                               annotation=annotation)
    else:
      cmds.shelfButton(currItem, edit=True,
                       image=image,
                       annotation=annotation, imageOverlayLabel=label,
                       overlayLabelColor=labelColor,
                       overlayLabelBackColor=labelBackColor,
                       backgroundColor=itemBackColor,
                       enableBackground=customBackColor,
                       enableCommandRepeat=cmds.checkBoxGrp(self.wItemRepeatable,
                                                            query=True, value1=True)
                       , sourceType=lang
                       , command=cmds.scrollField(self.wCommand,
                                                query=True, text=True)
                       )
      cmds.shelfButton(currItem, edit=True,
                       sourceType=langDbl,
                       doubleClickCommand=cmds.scrollField(self.wDblClkCommand,
                                                           query=True,
                                                           text=True))

      # Update the item preview:
      cmds.iconTextStaticLabel(self.wItemImage, edit=True,
                               annotation=annotation,
                               imageOverlayLabel=label,
                               overlayLabelColor=labelColor,
                               overlayLabelBackColor=labelBackColor,
                               backgroundColor=itemBackColor,
                               enableBackground=customBackColor)

  # ---------------------------------------------------------------------------
  def saveAllShelves(self, data):
    'Save the shelves'
    self.info('saveAllShelves data=%s' % data)
    cmds.saveAllShelves(self.mainShelfLayout)
    self.close('')

  # ---------------------------------------------------------------------------
  def close(self, data):
    'Close the window'
    self.info('close data=%s' % data)
    utils.executeDeferred(cmds.deleteUI , self.winName)

  # ---------------------------------------------------------------------------
  def currentShelf(self, short=False):
    """Return the current shelf widget, or None. When short is True we
    return only the name of the widget in the layout, otherwise the
    full path of the widget is returned.
    """
    indx = self.selectedIndex(self.wShelfList)
    shelves = cmds.tabLayout(self.mainShelfLayout, query=True, childArray=True)
    if (indx is None) or (shelves is None):
      self.info('currentShelf: No shelf selected')
      return None

    res = shelves[indx-1]
    if short:
      return res
    return self.mainShelfLayout+"|"+res

  # ---------------------------------------------------------------------------
  def currentShelfName(self):
    'Return the current shelf user defined name, or None'
    labels = cmds.tabLayout(self.mainShelfLayout, query=True, tabLabel=True)
    sel = cmds.textScrollList(self.wShelfList, query=True,
                              selectIndexedItem=True)
    if (sel is None) or (len(sel) < 1):
      self.info('currentShelfName: No shelf selected')
      return ""

    return labels[sel[0]-1]

  # ---------------------------------------------------------------------------
  def currentItem(self, short=False):
    'Return the current item, or None'

    shelf = self.currentShelf()
    if shelf is None:
      return None

    itemList = cmds.shelfLayout(shelf, query=True, childArray=True)
    indx = self.selectedIndex(self.wItemList)
    if indx is None:
      return None

    # Indices are 1-based in Maya UI calls
    indx = indx-1

    self.info("currentItem: %s %d" % (shelf, indx))
    if (indx >=0) and (indx < len(itemList)):
      if short:
        return itemList[indx]
      return shelf+"|"+itemList[indx]

    return None

  # ---------------------------------------------------------------------------
  def currentItemName(self):
    'Return the current item, or None'
    currItem = self.currentItem()
    if currItem is None:
      return ""

    if cmds.toolButton(currItem, exists=True ):
      # We have a tool button; use the tool name
      #
      return cmds.toolButton(currItem, query=True, tool=True)
    elif cmds.separator(currItem, exists=True):
      return 'Separator'
    else:
      return cmds.shelfButton(currItem, query=True, label=True)

  # ---------------------------------------------------------------------------
  def updateShelfList(self, at=1):
    'Recompute the shelf list'
    cmds.textScrollList(self.wShelfList, edit=True, removeAll=True)
    labels = cmds.tabLayout(self.mainShelfLayout, query=True, tabLabel=True)
    for name in labels:
      cmds.textScrollList(self.wShelfList, edit=True, append=name)
    cmds.textScrollList(self.wShelfList, edit=True, selectIndexedItem=at)
    self.selectShelf()

  # ---------------------------------------------------------------------------
  def updateItemList(self, at=1, atItem=None):
    atIndex = at
    """Update the item list based on the current shelf. If at is not
    None, this is the element number that needs to be reselecetd
    and made visible. If atItem is a shelfButton on this shelf, select it.
    """
    cmds.textScrollList(self.wItemList, edit=True, removeAll=True)

    curShelf = self.currentShelf()
    if curShelf is not None:
      self.info('updateItemList: Listing contents of "%s"' % curShelf)
      itemList = cmds.shelfLayout(curShelf, query=True, childArray=True)

      # Shelves are built as user clicked on them. Enforce creation of
      # all shelves if the one the user selected is still empty.
      if itemList is None:
        index = self.selectedIndex(self.wShelfList)
        if index is not None:
          mel.eval('loadShelf(%d)' % index)
        itemList = cmds.shelfLayout(curShelf, query=True, childArray=True)
        # If the creation failed, use an empty list
        if itemList is None:
          itemList = []

      index = 1
      for item in itemList:
        if atItem != None:
          if (atItem == item) or ((curShelf+'|'+item) == atItem):
            atIndex = index
        if cmds.toolButton(item, exists=True ):
          # We have a tool button; use tool name
          #
          itemName = cmds.toolButton(item, query=True, tool=True)
        elif cmds.shelfButton(item, exists=True):
          itemName = cmds.shelfButton(item, query=True, label=True)
        elif cmds.separator(item, exists=True):
          itemName = 'Separator'
        else:
          itemName = None
        if (itemName == '') or (itemName == None):
          itemName = '   '

        if itemName is not None:
          cmds.textScrollList(self.wItemList, edit=True, append=itemName)
          index = index + 1
      if (atIndex is not None) and (atIndex>0) and (atIndex<=len(itemList)):
        self.info("setting item list to %d" % atIndex)
        cmds.textScrollList(self.wItemList, edit=True,
                            selectIndexedItem=atIndex, showIndexedItem=atIndex)
        currItem = self.currentItemName()
        # Only true shelfButtons (i.e., not toolButtons) have editable names
        #
        cmds.textFieldGrp(self.wItemName, edit=True, text=currItem, enable=cmds.shelfButton( self.currentItem(), exists=True ))

    self.updateItemData()

  # ---------------------------------------------------------------------------
  def updateItemData(self):
    'Update the item values when the selected item changed'
    currItem = self.currentItem()

    # If nothing is selected, clear and dim all fields
    if (currItem is None) or cmds.separator(currItem, exists=True):
      self.info('updateItemData: No current item')
      cmds.text(self.wItemPreviewLabel, edit=True, enable=False)
      cmds.iconTextStaticLabel(self.wItemImage, edit=True, enable=False,
                               annotation='', imageOverlayLabel='',
                               image="commandButton.png",
                               backgroundColor=(.4, .4, .4))
      cmds.text(self.wIconNameLabel, edit=True, enable=False)
      cmds.symbolButton(self.wItemButton, edit=True, enable=False)
      cmds.symbolButton(self.wItemResButton, edit=True, enable=False)
      cmds.textField(self.wIconName, edit=True, enable=False, text='')
      cmds.textFieldGrp(self.wItemTip, edit=True, enable=False, text='')
      cmds.textFieldGrp(self.wItemLabel, edit=True, enable=False, text='')
      cmds.colorSliderGrp(self.wItemLabelColor, edit=True, enable=False,
                          rgbValue=self.defaultRGB)
      cmds.colorSliderGrp(self.wItemLabelBckColor, edit=True, enable=False,
                          rgbValue=self.defaultRGB)
      cmds.checkBoxGrp(self.wItemUserColor, edit=True, enable=False,
                       value1=False)
      cmds.colorSliderGrp(self.wItemBckColor, edit=True, enable=False,
                          rgbValue=self.defaultRGB)
      cmds.floatSliderGrp(self.wItemLabelBckTransp, edit=True, enable=False,
                          value=.25)
      cmds.checkBoxGrp(self.wItemRepeatable, edit=True, enable=False,
                       value1=False)
      cmds.radioButtonGrp(self.wLanguage, edit=True, enable=False,
                          select=1)
      cmds.radioButtonGrp(self.wLanguageDbl, edit=True, enable=False,
                          select=1)
      cmds.scrollField(self.wCommand, edit=True, enable=False, text='')
      cmds.scrollField(self.wDblClkCommand, edit=True, enable=False, text='')
      self.clearMenuItemData()
      cmds.textScrollList(self.wMenuItemList, edit=True, enable=False,
                          removeAll=True) 

      return
    elif cmds.toolButton(currItem, exists=True ):
      # Tool buttons have to be handled differently
      #
      queryItem = partial(cmds.toolButton, currItem, query=True)
      annotation =     queryItem(annotation=True)
      image1 =         queryItem(image1=True)
      label =          queryItem(imageOverlayLabel=True)
      itemBackColor =  queryItem(backgroundColor=True)
      cmds.text(self.wItemPreviewLabel, edit=True, enable=True)
      cmds.iconTextStaticLabel(self.wItemImage, edit=True, enable=True,
                               image=image1, annotation=annotation)
      cmds.text(self.wIconNameLabel, edit=True, enable=True)
      cmds.symbolButton(self.wItemButton, edit=True, enable=True)
      cmds.symbolButton(self.wItemResButton, edit=True, enable=True)

      cmds.textField(self.wIconName, edit=True, enable=True, text=image1)
      cmds.textFieldGrp(self.wItemTip, edit=True, enable=False, text=annotation)
      cmds.textFieldGrp(self.wItemLabel, edit=True, enable=False, text='')
      cmds.colorSliderGrp(self.wItemLabelColor, edit=True, enable=False)
      cmds.colorSliderGrp(self.wItemLabelBckColor, edit=True, enable=False)
      cmds.floatSliderGrp(self.wItemLabelBckTransp, edit=True, enable=False)
      cmds.checkBoxGrp(self.wItemUserColor, edit=True, enable=False)
      cmds.colorSliderGrp(self.wItemBckColor, edit=True, enable=False)
      cmds.checkBoxGrp(self.wItemRepeatable, edit=True, enable=False)
      cmds.radioButtonGrp(self.wLanguage, edit=True, enable=False)
      cmds.radioButtonGrp(self.wLanguageDbl, edit=True, enable=False)
      cmds.scrollField(self.wCommand, edit=True, enable=False, text='Command not editable for a toolButton')
      cmds.scrollField(self.wDblClkCommand, edit=True, enable=False, text='Double click command not editable for a toolButton')
      self.clearMenuItemData()
      cmds.scrollField( self.wMenuItemCommand, edit=True, enable=False, text='Popup Menu Items not editable for a toolButton')
      cmds.textScrollList(self.wMenuItemList, edit=True, enable=False,
                          removeAll=True) 
      return


    # We have a real item, update the values and remove dimming
    self.info('updateItemData: Getting values for button "%s"' % currItem)
    queryItem = partial(cmds.shelfButton, currItem, query=True)

    annotation =     queryItem(annotation=True)
    image =          queryItem(image=True)
    label =          queryItem(imageOverlayLabel=True)
    labelColor =     queryItem(overlayLabelColor=True)
    labelBackColor = queryItem(overlayLabelBackColor=True)
    itemBackColor =  queryItem(backgroundColor=True)
    customBackColor = queryItem(enableBackground=True)

    cmds.text(self.wItemPreviewLabel, edit=True, enable=True)
    cmds.iconTextStaticLabel(self.wItemImage, edit=True, enable=True,
                             image=queryItem(image=True),
                             overlayLabelColor=labelColor,
                             overlayLabelBackColor=labelBackColor,
                             backgroundColor=itemBackColor,
                             enableBackground=customBackColor,
                             annotation=annotation, imageOverlayLabel=label)
    cmds.text(self.wIconNameLabel, edit=True, enable=True)
    cmds.symbolButton(self.wItemButton, edit=True, enable=True)
    cmds.symbolButton(self.wItemResButton, edit=True, enable=True)

    lang = 1
    if queryItem(sourceType=True, command=True) == "python":
      lang = 2
    langDbl = 1
    if queryItem(sourceType=True, doubleClickCommand=True) == "python":
      langDbl = 2
    cmds.textField(self.wIconName, edit=True, enable=True, text=image)
    cmds.textFieldGrp(self.wItemTip, edit=True, enable=True, text=annotation)
    cmds.textFieldGrp(self.wItemLabel, edit=True, enable=True, text=label)
    cmds.colorSliderGrp(self.wItemLabelColor, edit=True, enable=True,
                        rgbValue=labelColor)
    cmds.colorSliderGrp(self.wItemLabelBckColor, edit=True, enable=True,
                        rgbValue=(labelBackColor[0],
                                  labelBackColor[1],
                                  labelBackColor[2]))
    cmds.floatSliderGrp(self.wItemLabelBckTransp, edit=True, enable=True,
                        value=labelBackColor[3])
    cmds.checkBoxGrp(self.wItemUserColor, edit=True, enable=True,
                     value1=customBackColor)
    cmds.colorSliderGrp(self.wItemBckColor, edit=True, enable=customBackColor,
                        rgbValue=itemBackColor)
    cmds.checkBoxGrp(self.wItemRepeatable, edit=True, enable=True,
                     value1=queryItem(enableCommandRepeat=True))
    cmds.radioButtonGrp(self.wLanguage, edit=True, enable=True, select=lang)
    cmds.radioButtonGrp(self.wLanguageDbl, edit=True, enable=True, select=langDbl)
    cmds.scrollField(self.wCommand, edit=True, enable=True,
                     text=queryItem(command=True))
    cmds.scrollField(self.wDblClkCommand, edit=True, enable=True,
                     text=queryItem(doubleClickCommand=True))

    cmds.textScrollList(self.wMenuItemList, edit=True, enable=True)
    nonDefaultItems = self.updateMenuItemList()
    if nonDefaultItems is None:
      currMenuItem = None
    else:
      currMenuItem = self.currentMenuItem( currentList=nonDefaultItems )

    if currMenuItem is None:
      self.clearMenuItemData()
    else:
      self.updateMenuItemData(currMenuItem)


  # ---------------------------------------------------------------------------
  def helpOnShelf(self, data):
    "Post the help for this window"
    cmds.showHelp("ShelfEditor")

  # ---------------------------------------------------------------------------
  def createMenus(self):
    "Create the menus for the Shelf editor"

    #  Add an options menu for shelf preferences
    cmds.menu(label=maya.stringTable['y_shelfEditorWindow.kOptions' ], tearOff=True)

    # Item style
    shelfItemLayout = cmds.optionVar(query='shelfItemStyle')

    cmds.radioMenuItemCollection()
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kIconOnly' ],
                  radioButton=(shelfItemLayout=='iconOnly'),
                  command=partial(self.setStyle, 'iconOnly'))
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kTextOnly' ],
                  radioButton=(shelfItemLayout=='textOnly'),
                  command=partial(self.setStyle, 'textOnly'))
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kTextBelow' ],
                  radioButton=(shelfItemLayout=='iconAndTextVertical'),
                  command=partial(self.setStyle, 'iconAndTextVertical'))
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kTextBeside' ],
                  radioButton=(shelfItemLayout=='iconAndTextHorizontal'),
                  command=partial(self.setStyle, 'iconAndTextHorizontal'))

    cmds.menuItem(divider=True)

    #  shelf saving
    saveMode = cmds.optionVar(query='isShelfSave')

    cmds.radioMenuItemCollection()
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kSaveAutomatically' ],
                  radioButton=saveMode,
                  command=partial(self.setSaveMode, 1))
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kSaveonRequest' ],
                  radioButton=not saveMode,
                  command=partial(self.setSaveMode, 0))

    cmds.setParent('..', menu=True)

    cmds.menu(label=maya.stringTable['y_shelfEditorWindow.kHelp' ], helpMenu=True)
    cmds.menuItem(label=maya.stringTable['y_shelfEditorWindow.kHelponShelves' ],
                  enableCommandRepeat=False,
                  command=self.helpOnShelf)

    cmds.setParent('..', menu=True)

  # ---------------------------------------------------------------------------
  def makeTwoColumns(self, form, child1, child2):
    "Attachment for a form to create two columns of the same size"
    cmds.formLayout(form, edit=True,
                    attachForm=[(child1, 'left', 0),
                                (child2, 'right', 0),

                                (child1, 'top', 0), (child1, 'bottom', 0),
                                (child2, 'top', 0), (child2, 'bottom', 0)
                                ],
                    attachPosition=[(child1, 'right', 0, 50)],
                    attachControl=[(child2, 'left', 5, child1)]
                    )

  # ---------------------------------------------------------------------------
  def makeResizableColumn(self, form, children,
                          left=None, right=None):
    """Attachment for a form to create a column where the last element
    is resizable.
    If left or right arrays are passed in, they should be set to
    Boolean arrays that define if each of the children needs to be
    attached to the left or to the right. They must have the same size
    as 'children'.
    """
    size = len(children)
    attachFormArray = [(children[0], 'top', 0),
                       (children[size-1], 'bottom', 0)]
    for i in xrange(size):
      if (left is None) or left[i]:
        attachFormArray.append((children[i], 'left', 0))
      if (right is None) or right[i]:
        attachFormArray.append((children[i], 'right', 0))

    attachControlArray = [(children[i+1], 'top', 5, children[i])
                          for i in xrange(size-1)]

    cmds.formLayout(form, edit=True,
                    attachForm=attachFormArray,
                    attachControl=attachControlArray)

  # ---------------------------------------------------------------------------
  def createShelfLists(self):
    "Create Shelf list and the shelf contents list side by side"
    layout = cmds.formLayout(numberOfDivisions=100)

    # Shelf list
    child1 = cmds.frameLayout(label=maya.stringTable['y_shelfEditorWindow.kShelfList' ])
    form = cmds.formLayout()

    # Add the buttons
    buttonForm = cmds.formLayout()
    buttons = cmds.rowLayout(numberOfColumns=4)
    cmds.symbolButton(image="moveLayerUp.png", annotation=self.moveUpStr,
                      command=partial(self.moveShelf, -1))
    cmds.symbolButton(image="moveLayerDown.png", annotation=self.moveDownStr,
                      command=partial(self.moveShelf, 1))
    cmds.symbolButton(image="newLayerEmpty.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kNewShelf' ],
                      command=self.newShelf)
    cmds.symbolButton(image="smallTrash.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kDeleteShelf' ],
                      command=self.deleteShelf)
    cmds.setParent('..')                    # rowLayout
    cmds.setParent('..')                    # formLayout

    cmds.formLayout(buttonForm, edit=True,
                    attachForm=[(buttons, 'right', 0),
                                (buttons, 'top', 0),
                                (buttons, 'bottom', 0)
                                ]
                    )

    # Shelf name
    self.wShelfName = cmds.textFieldGrp(label=maya.stringTable['y_shelfEditorWindow.kShelfName' ],
                                        adjustableColumn=2,
                                        columnAttach=[(1, "right", 5), (2, "both", 0)],
                                        columnWidth=[(1, 75), (2, 75)],
                                        changeCommand=self.shelfName)
										
    # Shelf alignment
    self.wShelfAlign = cmds.optionMenuGrp(label=maya.stringTable['y_shelfEditorWindow.kShelfAlignment' ],
									    adjustableColumn=2,
									    columnAttach=[(1, "right", 5), (2, "both", 0)],
									    columnWidth=[(1, 75), (2, 75)],
									    changeCommand=self.shelfAlignment)
    cmds.menuItem( label=maya.stringTable['y_shelfEditorWindow.kShelfLeft' ] )
    cmds.menuItem( label=maya.stringTable['y_shelfEditorWindow.kShelfRight' ] )

    # Add the shelf list
    self.wShelfList = cmds.textScrollList(numberOfRows=11,
                                          allowMultiSelection=False,
                                          deleteKeyCommand=partial(self.deleteShelf, 0),
                                          selectCommand=self.selectShelf)

    cmds.setParent('..')                    # formLayout

    # Now compute the attachments
    self.makeResizableColumn(form,
                             [buttonForm, self.wShelfName, self.wShelfAlign, self.wShelfList])
    cmds.setParent('..')                    # frameLayout


    # Shelf Contents
    child2 = cmds.frameLayout(label=maya.stringTable['y_shelfEditorWindow.kShelfContent' ])
    form = cmds.formLayout()

    buttonForm = cmds.formLayout()
    buttons = cmds.rowLayout(numberOfColumns=4)
    cmds.symbolButton(image="moveLayerUp.png", annotation=self.moveUpStr,
                      command=partial(self.moveItem, -1))
    cmds.symbolButton(image="moveLayerDown.png", annotation=self.moveDownStr,
                      command=partial(self.moveItem, 1))
    cmds.symbolButton(image="newLayerEmpty.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kNewItem' ],
                      command=self.newItem)
    cmds.symbolButton(image="smallTrash.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kDeleteItem' ],
                      command=self.deleteItem)
    cmds.setParent('..')                    # rowLayout
    cmds.setParent('..')                    # formLayout

    cmds.formLayout(buttonForm, edit=True,
                    attachForm=[(buttons, 'right', 0),
                                (buttons, 'top', 0),
                                (buttons, 'bottom', 0)
                                ]
                    )

    # Item name
    self.wItemName = cmds.textFieldGrp(label=maya.stringTable['y_shelfEditorWindow.kItemName' ],
                                       adjustableColumn=2,
                                       columnAttach=[(1, "right", 5), (2, "both", 0)],
                                       columnWidth=[(1, 75), (2, 75)],
                                       changeCommand=self.itemName)

    # Add the item list
    self.wItemList = cmds.textScrollList(numberOfRows=11,
                                         allowMultiSelection=False,
                                         deleteKeyCommand=partial(self.deleteItem, 0),
                                         selectCommand=self.selectItem)


    cmds.setParent('..')                    # formLayout

    # Now compute the attachments
    self.makeResizableColumn(form,
                             [buttonForm, self.wItemName, self.wItemList])

    cmds.setParent('..')                    # frameLayout

    self.makeTwoColumns(layout, child1, child2)
    cmds.setParent('..')                    # formLayout

    return layout

  # ---------------------------------------------------------------------------
  def createShelfPreview(self):
    "Create the controls for the preview icon"

    layout = cmds.rowLayout(numberOfColumns=2,
                            columnWidth=(1, self.col1width),
                            columnAttach=(1, "both", 0))
    self.wItemPreviewLabel = cmds.text(align="right",
                                       label=maya.stringTable['y_shelfEditorWindow.kIcon' ])
    self.wItemImage = cmds.iconTextStaticLabel(image="commandButton.png")
    cmds.setParent('..')                    # rowLayout

    return layout

  # ---------------------------------------------------------------------------
  def createIconNameControls(self):
    "Create the controls for the icon name"
    layout = cmds.rowLayout(numberOfColumns=4, adjustableColumn=2,
                            columnWidth=(1, self.col1width),
                            columnAttach=(1, "both", 0))

    self.wIconNameLabel = cmds.text(align="right",
                                    label=maya.stringTable['y_shelfEditorWindow.kIconName' ])
    self.wIconName = cmds.textField(changeCommand=self.itemData)

    self.wItemButton = cmds.symbolButton(image='fileOpen.png',
                                         annotation=maya.stringTable['y_shelfEditorWindow.kBrowseImage' ],
                                         command=partial(self.itemIcon, False))
    self.wItemResButton = cmds.symbolButton(image='factoryIcon.png',
                                            annotation=maya.stringTable['y_shelfEditorWindow.kMayaIcons' ],
                                            command=partial(self.itemIcon, True))
    cmds.setParent('..')                    # rowLayout

  # ---------------------------------------------------------------------------
  def createShelfData(self):
    "Create the controls for the current shelf item"
    
    itemLayout = cmds.columnLayout(adjustableColumn=True)

    self.createIconNameControls()

    self.wItemTip = cmds.textFieldGrp(
      label=maya.stringTable['y_shelfEditorWindow.kItemTooltip' ],
      adjustableColumn=2,
      columnWidth=(1, self.col1width),
      columnAttach=(2, "both", 0),
      changeCommand=self.itemData)

    self.wItemLabel = cmds.textFieldGrp(
      label=maya.stringTable['y_shelfEditorWindow.kItemLabel' ],
      adjustableColumn=2,
      columnWidth=(1, self.col1width),
      columnAttach=(2, "both", 0),
      changeCommand=self.itemData)

    self.wItemLabelColor = cmds.colorSliderGrp(
      label=maya.stringTable['y_shelfEditorWindow.kTextColor' ],
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)

    self.wItemLabelBckColor = cmds.colorSliderGrp(
      label=maya.stringTable['y_shelfEditorWindow.kBackgroundColor' ],
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)

    self.wItemLabelBckTransp = cmds.floatSliderGrp(
      label=maya.stringTable['y_shelfEditorWindow.kBackgroundTransparency' ],
      columnWidth=(1, self.col1width),
      field=True, minValue=0, maxValue=1.,
      changeCommand=self.itemData)

    self.wItemUserColor = cmds.checkBoxGrp(
      label=maya.stringTable['y_shelfEditorWindow.kItemUserColor' ],
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)
    self.wItemBckColor = cmds.colorSliderGrp(
      label=maya.stringTable['y_shelfEditorWindow.kButtonBackgroundColor' ],
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)

    self.wItemRepeatable = cmds.checkBoxGrp(
      label="", label1=maya.stringTable['y_shelfEditorWindow.kRepeatable' ],
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)

    cmds.setParent('..')                    # columnLayout

    return itemLayout

  # ---------------------------------------------------------------------------
  def createCommandTabs(self):
    "Create the layouts to edit the commands"
    form1 = cmds.formLayout()
    langStr = maya.stringTable['y_shelfEditorWindow.kLanguage' ]
    self.wLanguage = cmds.radioButtonGrp(
      label=langStr,
      numberOfRadioButtons=2,
      labelArray2=("MEL", "Python"),
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)
    self.wCommand = cmds.scrollField(height=80, width=200, enable=False,
                                     changeCommand=self.itemData)
    cmds.setParent('..')
    self.makeResizableColumn(form1, [
                                     self.wLanguage, 
                                                     self.wCommand])

    form2 = cmds.formLayout()
    self.wLanguageDbl = cmds.radioButtonGrp(
      label=langStr,
      numberOfRadioButtons=2,
      labelArray2=("MEL", "Python"),
      columnWidth=(1, self.col1width),
      changeCommand=self.itemData)
    self.wDblClkCommand = cmds.scrollField(height=80, width=200, enable=False,
                                           changeCommand=self.itemData)
    cmds.setParent('..')
    self.makeResizableColumn(form2, [
                                     self.wLanguageDbl, 
                                                     self.wDblClkCommand])

    return [form1, form2]

  # ---------------------------------------------------------------------------
  def createButtons(self):
    "Create the bottom buttons"

    form = cmds.formLayout(numberOfDivisions=100)

    b1 = cmds.button(label=maya.stringTable['y_shelfEditorWindow.kSaveAllShelves' ],
                command=self.saveAllShelves)
    b2 = cmds.button(label=maya.stringTable['y_shelfEditorWindow.kClose' ],
                command=self.close)

    self.makeTwoColumns(form, b1, b2)
    cmds.setParent('..')                    # rowLayout

    return form

  # ---------------------------------------------------------------------------
  def moveMenuItem(self, direction, data):
    'Move the current menu item in the given direction'
    self.info('moveMenuItem direction=%d, data=%s' % (direction, data))

    currIndex = self.selectedIndex(self.wMenuItemList)
    if currIndex is None:
      return

    # Get the non-default menuItem list
    #
    nonDefaultList = self.currentMenuItemList()
    if nonDefaultList is None:
      return

    numItems = len(nonDefaultList)

    if numItems == 0:
      return

    otherIndex = currIndex + direction
    if (otherIndex < 1) or (otherIndex > numItems):
      return

    # Swap the items
    currItem = nonDefaultList[currIndex-1]
    otherItem = nonDefaultList[otherIndex-1]
    otherLabel = cmds.menuItem( otherItem, query=True, label=True )
    otherCmd = cmds.menuItem( otherItem, query=True, command=True )
    otherSrcType = cmds.menuItem( otherItem, query=True, sourceType=True )

    cmds.menuItem( otherItem, edit=True,
        label=cmds.menuItem( currItem, query=True, label=True),
        sourceType=cmds.menuItem( currItem, query=True, sourceType=True),
        command=cmds.menuItem( currItem, query=True, command=True) )

    cmds.menuItem( currItem, edit=True, label=otherLabel,
                    command=otherCmd, sourceType=otherSrcType )

    self.updateMenuItemList(at=otherIndex)

  # ---------------------------------------------------------------------------
  def currentPopup(self, short=False):
    'Returns the popupMenu associated with the current button, if any'
    currItem = self.currentItem()
    if currItem is None:
      return None

    # Is the item selected a shelf button?
    #
    if not cmds.shelfButton(currItem, exists=True ):
      return None

    # Does the shelf button have at least one popup menu?
    #
    menus = cmds.shelfButton( currItem, query=True, pma=True )
    if (menus is None) or (len(menus) == 0):
      return None
    menu = menus[0]
    return menu

  # ---------------------------------------------------------------------------
  def newMenuItem(self, data):
    'Create a new menuItem'
    self.info('newMenuItem data=%s' % data)

    menu = self.currentPopup()
    if menu is None:
      # All shelfButtons should have a menu; bail if it's not there
      return

    # Add new item at the end
    #
    currIndex = self.selectedIndex(self.wMenuItemList)

    newItem = cmds.menuItem(parent=menu)

    nonDefaultList = self.updateMenuItemList()
    # Get the non-default menuItem list
    #
    if nonDefaultList is None:
      # This should never happen, since we just added one item
      #
      return

    numMenuItems = len(nonDefaultList)
    # Select last item
    #
    cmds.textScrollList(self.wMenuItemList,edit=True,selectIndexedItem=numMenuItems)

    prevIndex = numMenuItems - 1

    shuffle = True
    if currIndex is None:
      # Nothing was selected, adding to the end is fine
      #
      shuffle = False
    else:
      shuffle = prevIndex > currIndex

    if shuffle:
      cmds.textScrollList(self.wMenuItemList, edit=True, visible=False)
      while prevIndex > currIndex:
        # Move prev item to the prev+1 item

        currItem = nonDefaultList[prevIndex]
        prevItem = nonDefaultList[prevIndex-1]

        cmds.menuItem( currItem, edit=True,
            label=cmds.menuItem( prevItem, query=True, label=True),
            sourceType=cmds.menuItem( prevItem, query=True, sourceType=True),
            command=cmds.menuItem( prevItem, query=True, command=True) )

        prevIndex = prevIndex - 1
      cmds.textScrollList(self.wMenuItemList, edit=True, visible=True)
    cmds.menuItem( nonDefaultList[prevIndex], edit=True,
                       label="User menuItem",
                       command='print("User defined menuItem");',
                       sourceType='MEL')
    self.updateMenuItemList(at=(prevIndex+1))

  # ---------------------------------------------------------------------------
  def deleteMenuItem(self, data):
    'Delete the current menu item'
    self.info('deleteMenuItem data=%s' % data)

    currMenuItem = self.currentMenuItem()
    index = self.selectedIndex(self.wMenuItemList)
    if currMenuItem is None or index is None:
      return
    cmds.deleteUI(currMenuItem)
    self.clearMenuItemData()

    menu = self.currentPopup()
    if menu is None:
      cmds.textScrollList(self.wMenuItemList, edit=True, removeAll=True)
      return

    if index > cmds.popupMenu( menu, query=True, numberOfItems=True ):
      index = index - 1
    self.info('\tdeleteMenuItem: index is %d' % index)

    self.updateMenuItemList(at=index)

  # ---------------------------------------------------------------------------
  def selectMenuItem(self):
    'Select a new menuItem'
    self.info('selectMenuItem')
    item = self.currentMenuItem()
    if item is None:
      return
    if not cmds.menuItem( item, exists=True ):
      return
    self.updateMenuItemData(item)

  # ---------------------------------------------------------------------------
  def renameMenuItem(self, data):
    'Rename the current menu item'
    name = cmds.textFieldGrp(self.wMenuItemName, query=True, text=True)
    currMenuItem = self.currentMenuItem()
    if currMenuItem is None:
      return
    currIndx = self.selectedIndex(self.wMenuItemList)
    if cmds.menuItem(currMenuItem, exists=True ):
      # We have a menuItem, go ahead and update the name
      #
      cmds.menuItem(currMenuItem, edit=True, label=name)
    self.updateMenuItemList(at=currIndx)

  # ---------------------------------------------------------------------------
  def changeMenuItemData(self, data):
    'Change the current menuItem data'
    self.info('changeMenuItemData data=%s' % data)

    currMenuItem = self.currentMenuItem()
    if currMenuItem is None:
      return

    langMenuItem = "mel"
    if cmds.radioButtonGrp(self.wMenuItemLanguage, query=True, select=True) == 2:
      langMenuItem = "python"
    cmds.menuItem( currMenuItem, edit=True,
                       sourceType=langMenuItem,
                       command=cmds.scrollField(self.wMenuItemCommand, query=True, text=True))

  # ---------------------------------------------------------------------------
  def currentMenuItem(self, short=False, currentList=None ):
    'Return the current menuItem, or None'

    # Get the non-default menuItem list
    #
    nonDefaultList = currentList
    if nonDefaultList is None:
      nonDefaultList = self.currentMenuItemList()
    if nonDefaultList is None:
      return None

    # Do we have a menu item selected?
    #
    indx = self.selectedIndex(self.wMenuItemList)
    if indx is None:
      return None

    # Indices are 1-based in Maya UI calls
    indx = indx-1

    if (indx >=0) and (indx < len(nonDefaultList)):
      if short:
        return nonDefaultList[indx]
      else:
        # Do we have a shelf item selected?
        #
        menu = self.currentPopup()
        if menu is None:
          return None
    
        return menu+"|"+nonDefaultList[indx]

    return None

  # ---------------------------------------------------------------------------
  def currentMenuItemName(self, menuItem=None):
    'Return the current menuItem name, or the empty string'
    currItem = menuItem
    if menuItem is None:
      currItem = self.currentMenuItem()
    if currItem is None:
      return ""
    return cmds.menuItem( currItem, query=True, label=True)

  # ---------------------------------------------------------------------------
  def currentMenuItemCommand(self, menuItem=None):
    'Return the current menuItem command, or the empty string'
    currItem = menuItem
    if menuItem is None:
      currItem = self.currentMenuItem()
    if currItem is None:
      return ""
    return cmds.menuItem( currItem, query=True, command=True)

  # ---------------------------------------------------------------------------
  def currentMenuItemList(self, at=1):
    'Returns a list of the current (non-default) menuItem(s) if any, o/w None'
    menu = self.currentPopup()
    if menu is None:
      return None

    numItems = cmds.popupMenu( menu, query=True, ni=True )
    if numItems == 0:
      return None

    # We have at least one menu item; ignore default ones, if any
    #

    itemList = cmds.popupMenu( menu, query=True, ia=True )
    nonDefaultList = []
    for item in itemList:
      if cmds.menuItem( item, query=True, divider=True ):
        continue
      itemName = cmds.menuItem( item, query=True, label=True)
      if itemName is not None:
        itemCommand = cmds.menuItem( item, query=True, command=True)
        # Note: The string used to identify default menu items needs to match
        # the one used in TshelfButtonCmd.cpp
        #
        # In Python menu item commands may be callables as well as strings,
        # so let's make sure that this one is a string before doing string
        # operations on it.
        #
        if isinstance(itemCommand, basestring) and itemCommand.startswith( '/*dSBRMBMI*/' ):
          continue
        nonDefaultList.append( item )
    if len(nonDefaultList) == 0:
      return None
    return nonDefaultList

  # ---------------------------------------------------------------------------
  def updateMenuItemList(self, at=1):
    """Update the menuItem list based on the current shelfButton. If at is not
    None, this is the element number that needs to be reselecetd
    and made visible.
    """
    cmds.textScrollList(self.wMenuItemList, edit=True, removeAll=True)
    nonDefaultItems = self.currentMenuItemList()
    if nonDefaultItems is None:
      return None

    index = 1
    for item in nonDefaultItems:
      itemName = cmds.menuItem( item, query=True, label=True)
      itemCommand = cmds.menuItem( item, query=True, command=True)
      cmds.textScrollList(self.wMenuItemList, edit=True, append=itemName)
      langMenuItem = 1
      if cmds.menuItem( item, query=True, sourceType=True) == "python":
        langMenuItem = 2
      if index==at:
        cmds.textFieldGrp( self.wMenuItemName, edit=True, enable=True, text=itemName)
        cmds.scrollField(self.wMenuItemCommand, edit=True, enable=True, text=itemCommand)
        cmds.textScrollList(self.wMenuItemList, edit=True, selectIndexedItem=index)
        cmds.radioButtonGrp(self.wMenuItemLanguage, edit=True, enable=True, select=langMenuItem)
      index = index + 1

    return nonDefaultItems

  # ---------------------------------------------------------------------------
  def updateMenuItemData(self, menuItem=None, doClear=False):
    """Update the menuItem values when the menuItem changed
    If doClear is true, clear all the entries.
    If menuItem is None, use the current menuItem
    """

    currMenuItem = menuItem
    if menuItem is None and not doClear:
      currMenuItem = self.currentMenuItem()
    doEnable = not (currMenuItem is None)
    langMenuItem = 1
    if doEnable:
      if cmds.menuItem( currMenuItem, query=True, sourceType=True) == "python":
        langMenuItem = 2
      name = self.currentMenuItemName(currMenuItem)
      cmd = self.currentMenuItemCommand(currMenuItem)
    else:
      name = ""
      cmd = ""
    cmds.textFieldGrp( self.wMenuItemName, edit=True, enable=doEnable,text=name)
    #if doEnable:
    #else:
    cmds.radioButtonGrp(self.wMenuItemLanguage, edit=True,enable=doEnable,
                            select=langMenuItem)
    cmds.scrollField(self.wMenuItemCommand, edit=True, enable=doEnable,text=cmd)

  # ---------------------------------------------------------------------------
  def clearMenuItemData(self):
    'Clear the menu item values when no item is selected'
    self.updateMenuItemData( doClear=True )

  # ---------------------------------------------------------------------------
  def createMenuItemsTab(self):
    "Create menuItem list and the menuItem command window side by side"

    # Create Popup Menu Items list
    layout = cmds.formLayout(numberOfDivisions=100)

    # Menu item list
    child1 = cmds.frameLayout(label=maya.stringTable['y_shelfEditorWindow.kMenuItems' ])
    form = cmds.formLayout()

    # Add the buttons
    buttonForm = cmds.formLayout()
    buttons = cmds.rowLayout(numberOfColumns=4)
    cmds.symbolButton(image="moveLayerUp.png", annotation=self.moveUpStr,
                      command=partial(self.moveMenuItem, -1))
    cmds.symbolButton(image="moveLayerDown.png", annotation=self.moveDownStr,
                      command=partial(self.moveMenuItem, 1))
    cmds.symbolButton(image="newLayerEmpty.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kNewMenuItem' ],
                      command=self.newMenuItem)
    cmds.symbolButton(image="smallTrash.png",
                      annotation=maya.stringTable['y_shelfEditorWindow.kDeleteMenuItem' ],
                      command=self.deleteMenuItem)
    cmds.setParent('..')                    # rowLayout
    cmds.setParent('..')                    # formLayout

    cmds.formLayout(buttonForm, edit=True,
                    attachForm=[(buttons, 'right', 0),
                                (buttons, 'top', 0),
                                (buttons, 'bottom', 0)
                                ]
                    )

    # Menu item name
    self.wMenuItemName = cmds.textFieldGrp(label=maya.stringTable['y_shelfEditorWindow.kMenuItemName' ],
                                       adjustableColumn=2,
                                       columnAttach=[(1, "right", 5), (2, "both", 0)],
                                       columnWidth=[(1, 75), (2, 75)],
                                       changeCommand=self.renameMenuItem)

    # Add the menu item list
    self.wMenuItemList = cmds.textScrollList(numberOfRows=11,
                                          allowMultiSelection=False,
                                          deleteKeyCommand=partial(self.deleteMenuItem, 0),
                                          selectCommand=self.selectMenuItem)
    cmds.setParent('..')                    # formLayout

    # Now compute the attachments
    self.makeResizableColumn(form,
                             [buttonForm, self.wMenuItemName, self.wMenuItemList])
    cmds.setParent('..')                    # frameLayout

    child2 = cmds.frameLayout(label=maya.stringTable['y_shelfEditorWindow.kMenuItemCommand' ])
    child2Form = cmds.formLayout()
    self.wMenuItemLanguage = cmds.radioButtonGrp(
      label=maya.stringTable['y_shelfEditorWindow.kLanguage2' ],
      numberOfRadioButtons=2,
      labelArray2=("MEL", "Python"),
      columnWidth=(1, 100),
      changeCommand=self.changeMenuItemData)
    self.wMenuItemCommand = cmds.scrollField(height=80, width=100, enable=False,
                                     changeCommand=self.changeMenuItemData)

    cmds.setParent('..')                    # formLayout

    # Now compute the attachments

    self.makeResizableColumn(child2Form, [
                                     self.wMenuItemLanguage, 
                                                     self.wMenuItemCommand])

    cmds.setParent('..')                    # frameLayout

    self.makeTwoColumns(layout, child1, child2)

    cmds.setParent('..')                    # formLayout

    return layout


  # ---------------------------------------------------------------------------
  def create(self, selectedShelfButton=None, selectedTabIndex=2):
    "Create the shelf editor window, optionally selecting button to edit"

    # Rebuild the window if it is still there. This is the easiest way
    # to init all variables
    if cmds.window(self.winName, exists=True) <> 0:
      cmds.deleteUI(self.winName)

    shelves = maya.stringTable['y_shelfEditorWindow.kShelves' ]
    cmds.window(self.winName,
                title=maya.stringTable['y_shelfEditorWindow.kShelfEditor' ],
                width=100, height=100,
                iconName=shelves, menuBar=True)
    self.createMenus()

    # Overall tabs
    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)

    form = cmds.formLayout(numberOfDivisions=100)

    lists = self.createShelfLists()
    preview = self.createShelfPreview()
    data = self.createShelfData()
    buttons = self.createButtons()

    cmds.setParent('..')                    # formLayout

    # Now compute the attachments
    cmds.formLayout(form, edit=True,
                    attachForm=[(lists, 'top', 5),
                                (buttons, 'bottom', 5),

                                (lists,   'left', 5), (lists,   'right', 5),
                                (preview, 'left', 5), (preview, 'right', 5),
                                (data,    'left', 5), (data,    'right', 5),
                                (buttons, 'left', 5), (buttons, 'right', 5),
                                ],
                    attachControl=[(preview, 'bottom', 5, data),
                                   (data, 'bottom', 5, buttons),
                                   (lists, 'bottom', 5, preview)]
                    )

    commandTabs = self.createCommandTabs()

    menuItemsTab = self.createMenuItemsTab()

    cmds.tabLayout(tabs, edit=True,
                   tabLabel=[(form,           shelves)
                           , (commandTabs[0], maya.stringTable['y_shelfEditorWindow.kShelfCommand' ])
                           , (commandTabs[1], maya.stringTable['y_shelfEditorWindow.kShelfDblCommand' ])
                           , (menuItemsTab, maya.stringTable['y_shelfEditorWindow.kShelfMenuItems' ])
                             ])
    cmds.setParent('..')                    # tabLayout

    currShelfIndx = cmds.tabLayout(self.mainShelfLayout, query=True, selectTabIndex=True)
    self.updateShelfList(at=currShelfIndx)
    if selectedShelfButton != None:
      self.updateItemList(atItem=selectedShelfButton)
      cmds.tabLayout(tabs, edit=True, selectTabIndex=selectedTabIndex )
    cmds.showWindow(self.winName)

# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
