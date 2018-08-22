"""
Color management preferences input space rules UI code.
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)


import maya.cmds as cmds
import maya.mel as mel
import maya.app.colorMgt.customTransformUI as customTransformUI
import maya.app.colorMgt.reapplyRules as reapplyRules
import re

vSpc = 10
hSpc = 10
buttonWidth = 60

# Parent form for the rules UI.
parentForm = ''

# Color constants
red = [1, 0, 0]
black = [0, 0, 0]

def mayaImageFileExtensions():
    """Return the list of image file extensions read by Maya."""

    # MAYA-48524 - LT: need to source the mel file containing buildImageFileFilterList.
    mel.eval('source fileDialogFilterTypes')

    # This MEL procedure returns a list of image file extensions in a file
    # dialog-friendly format, so we need to filter it.
    dialogImageFiles = mel.eval('buildImageFileFilterList')

    # Returned string has file type extensions within parentheses.
    extRe = re.compile('\((.*)\);')
    reMatch = extRe.search(dialogImageFiles)
    extensionsString = reMatch.group(1)
    baseExtensionsList = re.split('[\W]+', extensionsString)

    # The split regexp matches at the beginning of the string, so split
    # returns an empty string match as the initial split.  Throw that away.
    #
    baseExtensionsList = baseExtensionsList[1:]

    # Maya supported file extensions are case sensitive so the same file extension
    # is in lowercase and in uppercase in the list (i.e. two times). However file 
    # extensions with a mix of lower & upper cases are still not correctly handled.
    # To overcome that problem for the file rule mechanism, the list is changed to 
    # only display lowercase file extensions and the file rule evaluation is based
    # on lowercase characters.

    # Lower file extension characters & remove duplicated file extensions
    baseExtensionsList = [element.lower() for element in baseExtensionsList]
    baseExtensionsList = list(set(baseExtensionsList))

    # The '*' match all glob pattern must also be presented in the extension
    # menu.
    extensionsList = ['*'] 
    extensionsList[1:] = baseExtensionsList

    extensionsList.sort()

    return extensionsList
    
def nativeMode():
    return not cmds.colorManagementPrefs(query=True, cmConfigFileEnabled=True)

class Rule(object):

    def __init__(self, name):

        self.name = name

    def canDelete(self):
        # A non-deletable rule cannot be deleted or moved.
        return False

class OpaqueRule(Rule):

    def __init__(self, name):
        super(OpaqueRule, self).__init__(name=name)

    def createUI(self):
        handlerForm = cmds.setParent(query=True)
        layout = cmds.rowLayout()
        # Surprisingly, the simpler
        # cmds.columnLayout(columnAlign='center', rowSpacing=20)
        # is not equivalent to the line below, and doesn't center horizontally.
        cmds.rowColumnLayout(numberOfColumns=1, columnAlign=[1, 'center'],
                             rowSpacing=[1, 20])
        cmds.text(label=self.name)
        cmds.text(label=maya.stringTable['y_inputSpaceRulesUI.kOCIORuleLabel' ],
                  wordWrap=True)
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.formLayout(handlerForm, edit=True,
                        attachForm=[(layout, 'top', 0), (layout, 'bottom', 0)])

class ColorSpaceRule(Rule):

    def __init__(self, name):
        super(ColorSpaceRule, self).__init__(name=name)

        # State of color space background color.  True in case of invalid
        # color space.
        self._menuInvalidBgColor = False

    def setColorSpace(self, colorSpace):
        cmds.colorManagementFileRules(
            self.name, edit=True, colorSpace=colorSpace)

    def getColorSpace(self):
        return cmds.colorManagementFileRules(
            self.name, query=True, colorSpace=True)

    colorSpace = property(getColorSpace, setColorSpace)

    def onInputColorSpaceChange(self, *args):
        selection = cmds.optionMenuGrp(
            self._colorSpaceMenu, query=True, select=True)

        if selection == cmds.optionMenuGrp(
                self._colorSpaceMenu, query=True, numberOfItems=True):
            # Last entry is special: add custom transform.
            returnVal = customTransformUI.addCustomTransformDialog('input')

            # If user didn't cancel out, add to the menu, and change the color
            # space.  Awkward menuItem parent call taken from optionMenuGrp
            # documentation, more intuitive and direct
            # cmds.setParent(self._colorSpaceMenu, menu=True)
            # fails with object not found error.
            if returnVal != '':
                cmds.menuItem(parent=self._colorSpaceMenu + '|OptionMenu',
                              label=returnVal)
                self.colorSpace = returnVal

            cmds.optionMenuGrp(
                self._colorSpaceMenu, edit=True, value=self.colorSpace)

            validColorSpace = True
        else:
            # Not the last entry: standard processing.
            newColorSpace = cmds.optionMenuGrp(
                    self._colorSpaceMenu, query=True, value=True)

            validColorSpace = self.validateColorSpace(newColorSpace)

            if validColorSpace:
                self.colorSpace = newColorSpace

        self.setMenuValidColorSpace(validColorSpace)

    def onRemoveColorSpace(self, *args):
        # If color space is already invalid (doesn't exist), don't try to
        # remove it.
        if not self.validateColorSpace(self.colorSpace):
            return

        # Because color space removal can only be done on the selected
        # color space, it must be our own color space, so we must choose an
        # alternate one.
        removed = mel.eval(
            'colorMgtRemoveTransform "' + self.colorSpace + '" input')
            
        if removed != '':
            # Need a mode-specific interface to retrieve a default input
            # color space.  For now, arbitrarily pick the first one.
            inputSpaces = cmds.colorManagementPrefs(
                query=True, inputSpaceNames=True)
            self.colorSpace = inputSpaces[0]

    def validateColorSpace(self, colorSpace):
        inputSpaces = cmds.colorManagementPrefs(
            query=True, inputSpaceNames=True)

        return colorSpace in inputSpaces

    def setMenuValidColorSpace(self, valid):
        if valid:
            # If we were invalid, need to reset (but only if we were invalid).
            if self._menuInvalidBgColor:
                cmds.layout(self._colorSpaceLayout, edit=True,
                            backgroundColor=black, noBackground=False)
        else:
            cmds.layout(self._colorSpaceLayout, edit=True, backgroundColor=red)

        self._menuInvalidBgColor = not valid


    def createColorSpaceMenu(self):

        self._colorSpaceLayout = cmds.rowLayout(numberOfColumns=2)

        self._colorSpaceMenu = cmds.optionMenuGrp(columnWidth=[1, 130],
            ad2=2, label=maya.stringTable['y_inputSpaceRulesUI.kInputColorSpaceMenuLabel' ],
            changeCommand=self.onInputColorSpaceChange)

        # Fill in the input color spaces, and set the menu selection.
        inputSpaces = cmds.colorManagementPrefs(
            query=True, inputSpaceNames=True)

        for inputSpace in inputSpaces:
            cmds.menuItem(label=inputSpace)

        validColorSpace = self.colorSpace in inputSpaces
        if not validColorSpace:
            cmds.menuItem(label=self.colorSpace)

        addTransformLabel = mel.eval(
            'uiRes("m_colorManagementUtilities.kAddCustomTransform")')

        cmds.menuItem(enable=nativeMode(), label=addTransformLabel)

        cmds.optionMenuGrp(
            self._colorSpaceMenu, edit=True, value=self.colorSpace)

        self.setMenuValidColorSpace(validColorSpace)

        transformSettings = cmds.symbolButton(
            enable=nativeMode(), image='colorTransformSettings.png')

        cmds.popupMenu(button=1, parent=transformSettings)
        removeTransformLabel = mel.eval(
            'uiRes("m_createPrefWndUI.kColorManagementRemoveTransform")')
            
        cmds.menuItem(
            label=removeTransformLabel, command=self.onRemoveColorSpace)

        cmds.setParent('..', menu=True)

        # End of row layout.
        cmds.setParent('..')

    def fileRuleLayout(self, extWidget, patternWidget):
        """Shared layout for color space rules."""
    
        # Add in common widgets
        conditionText = cmds.text(
            label=maya.stringTable['y_inputSpaceRulesUI.kRuleConditionsLabel' ])
    
        separatorWidget = cmds.separator(style='singleDash')
    
        colorSpaceText = cmds.text(
            label=maya.stringTable['y_inputSpaceRulesUI.kImageInputColorSpace' ])
    
        # Get our parent form layout, and place the widgets inside it.
        handlerForm = cmds.setParent(query=True)
    
        rowSpacing = 30

        cmds.formLayout(
            handlerForm, edit=True,
            attachForm=[(conditionText,    'top',   vSpc),
                        (conditionText,    'left',  hSpc),
                        (extWidget,        'left',  hSpc),
                        (patternWidget,    'left',  hSpc),
                        (separatorWidget,  'left',  hSpc),
                        (separatorWidget,  'right', hSpc),
                        (colorSpaceText,   'left',  hSpc),
                        (self._colorSpaceLayout, 'left',  hSpc)],
            attachOppositeControl=[
                (extWidget,        'top', rowSpacing, conditionText),
                (patternWidget,    'top', rowSpacing, extWidget),
                (separatorWidget,  'top', rowSpacing, patternWidget)],
            attachControl=[
                (colorSpaceText,   'top', vSpc, separatorWidget),
                (self._colorSpaceLayout, 'top', vSpc, colorSpaceText)])


class DefaultRule(ColorSpaceRule):

    def __init__(self):
        rules = cmds.colorManagementFileRules(listRules=True)
        super(DefaultRule, self).__init__(rules[0])

    def createUI(self):

        extText = cmds.text(width=150, align='right',
            label=maya.stringTable['y_inputSpaceRulesUI.kDefaultRuleExtLabel' ])

        patternText = cmds.text(width=150, align='right',
            label=maya.stringTable['y_inputSpaceRulesUI.kDefaultRulePatternLabel' ])

        self.createColorSpaceMenu()

        # Fill in layout.
        self.fileRuleLayout(extText, patternText)

class FilePathRule(ColorSpaceRule):

    _extensionsList = mayaImageFileExtensions()

    def __init__(self, name):
        super(FilePathRule, self).__init__(name=name)
        if self.pattern == '':
            self.pattern = '*'

    def setPattern(self, pattern):
        cmds.colorManagementFileRules(
            self.name, edit=True, pattern=pattern)

    def getPattern(self):
        return cmds.colorManagementFileRules(
            self.name, query=True, pattern=True)

    pattern = property(getPattern, setPattern)

    def setExtension(self, extension):
        cmds.colorManagementFileRules(
            self.name, edit=True, extension=extension)

    def getExtension(self):
        return cmds.colorManagementFileRules(
            self.name, query=True, extension=True)

    extension = property(getExtension, setExtension)

    def canDelete(self):
        return True

    def onPatternChange(self, *args):
        self.pattern = cmds.textFieldGrp(
            self._patternWidget, query=True, text=True)
        if self.pattern == '':
            self.pattern = '*'
            cmds.textFieldGrp(self._patternWidget, edit=True, text=self.pattern)

    def onExtensionChange(self, *args):
        self.extension = cmds.optionMenuGrp(
            self._extensionsMenu, query=True, value=True)

    def createUI(self):
        self._extensionsMenu = cmds.optionMenuGrp(
            ad2=2, label=maya.stringTable['y_inputSpaceRulesUI.kExtensionsMenuLabel' ],
            changeCommand=self.onExtensionChange)

        # Fill in the extensions.
        for extension in FilePathRule._extensionsList:
            cmds.menuItem(label=extension)

        # Using the command, the user could select a file extension
        # which does not exist.
        try:
            cmds.optionMenuGrp(self._extensionsMenu, edit=True,
                               value=self.extension)
        except RuntimeError, err:
            cmds.optionMenuGrp(self._extensionsMenu, edit=True,
                               value=FilePathRule._extensionsList[0])
            err = maya.stringTable['y_inputSpaceRulesUI.kInvalidNode' ]
            msg = cmds.format(err, stringArg=(self.extension, FilePathRule._extensionsList[0]))
            cmds.warning( msg )

        self._patternWidget = cmds.textFieldGrp(
            ad2=2, label=maya.stringTable['y_inputSpaceRulesUI.kImageNamePattern'],
            changeCommand=self.onPatternChange, text=self.pattern)

        self.createColorSpaceMenu()

        # Fill in layout.
        self.fileRuleLayout(self._extensionsMenu, self._patternWidget)

class ChainRule(Rule):            

    def __init__(self, name=''):
        super(ChainRule, self).__init__(name=name)

        # Initialize our list of rules with a default rule.  This will
        # always be the last rule.  The rule list is always appended to,
        # and is placed in the scroll list in back to front (reverse
        # iteration) order.
        self._rulesChain = []
        self._rulesChain.append(DefaultRule())

        # Fill in UI with existing rules.
        rules = cmds.colorManagementFileRules(listRules=True)
        # Default rule already added, skip it.
        rules.pop(0)

        self._ocioRulesEnabled = cmds.colorManagementPrefs(query=True, cmConfigFileEnabled=True) \
                                 and cmds.colorManagementPrefs(query=True, ocioRulesEnabled=True)
        if self._ocioRulesEnabled:
            self._rulesChain.append(OpaqueRule(rules.pop(0)))
        else:
            for rule in rules:
                self._rulesChain.append(FilePathRule(rule))

        self._selectedPos = 0

    def isReadOnly(self):
        # A read-only container does not allow moving, adding, or deleting
        # rules.
        return self._ocioRulesEnabled and not nativeMode()

    def positionToIndex(self, position):
        # For SynColor, higher priority rules are at higher indices.  The
        # scroll list works in reverse (top to bottom), and its indexing 
        # is 1-based.
        return len(self._rulesChain) - position

    def indexToPosition(self, index):
        return len(self._rulesChain) - index

    def updateScrollList(self):
        # Naive, destroy everything and rebuild implementation, but should
        # not be an issue given limited size of rules list.  Note how we
        # must use reverse iteration, as rules appended to the rule list
        # must appear at the top of the scroll list.

        cmds.textScrollList(self._scrollList, edit=True, removeAll=True)

        for rule in reversed(self._rulesChain):
            cmds.textScrollList(self._scrollList, edit=True, append=rule.name)

    def appendRule(self, rule):

        self._rulesChain.append(rule)
        self.updateScrollList()
        self.selectRule(len(self._rulesChain)-1)

    def createHandlerRuleUI(self):

        # Re-create the rule UI.  First, delete existing children of the
        # handler rule form.
        children = cmds.formLayout(
            self._handlerForm, query=True, childArray=True)

        for child in children:
            cmds.deleteUI(child)

        # Next, call create UI on the selected rule.
        rule = self._rulesChain[self._selectedPos]

        oldParent = cmds.setParent(query=True)

        cmds.setParent(self._handlerForm)

        rule.createUI()

        cmds.setParent(oldParent)

    def updateHandlerRuleUI(self):

        # Update up, down, delete buttons.
        rule = self._rulesChain[self._selectedPos]

        canGoUp = not self.isReadOnly() and rule.canDelete() and (
            self._selectedPos < (len(self._rulesChain) - 1))
        canGoDown = not self.isReadOnly() and rule.canDelete() and (
            self._selectedPos > 1)
        canAdd    = not self.isReadOnly()
        canDelete = not self.isReadOnly() and rule.canDelete()

        cmds.button(self._up, edit=True, enable=canGoUp)
        cmds.button(self._down, edit=True, enable=canGoDown)
        cmds.button(self._add, edit=True, enable=canAdd)
        cmds.button(self._delete, edit=True, enable=canDelete)

        self.createHandlerRuleUI()

    def selectRule(self, position):

        self._selectedPos = position
        selectedIndex = self.positionToIndex(self._selectedPos)
        cmds.textScrollList(self._scrollList, edit=True,
                            selectIndexedItem=selectedIndex)

        self.updateHandlerRuleUI()

    def createUI(self):

        # Create a formLayout under our parent.  It will hold 3 controls,
        # the rules chain form, the separator, and the handler rule form.
        # Use 100 divisions as a convenience, so that divisions are
        # effectively a percentage.
        self._form = cmds.formLayout(numberOfDivisions=100)

        # Create a form layout for the rules chain section of the UI.
        self._chainForm = cmds.formLayout(numberOfDivisions=100)

        self._scrollList = cmds.textScrollList(
            allowMultiSelection=False, selectCommand=self.onSelect)

        self.updateScrollList()

        # Priority controls.
        self._priorityText = cmds.text(
            label=maya.stringTable['y_inputSpaceRulesUI.kPriorityLabel' ])
        self._up     = cmds.button(
            label=maya.stringTable['y_inputSpaceRulesUI.kUpLabel' ], width=buttonWidth, command=self.onUp)
        self._down   = cmds.button(
            label=maya.stringTable['y_inputSpaceRulesUI.kDownLabel' ], width=buttonWidth,
            command=self.onDown)
        self._add    = cmds.button(
            label=maya.stringTable['y_inputSpaceRulesUI.kAddLabel' ], width=buttonWidth,
            command=self.onAddRule)
        self._delete = cmds.button(
            label=maya.stringTable['y_inputSpaceRulesUI.kDeleteLabel' ], width=buttonWidth,
            command=self.onDeleteRule)

        # Reapply rules.
        self._reload = cmds.button(
            label=maya.stringTable['y_inputSpaceRulesUI.kReloadLabel' ],
            command=self.onReapply)

        cmds.formLayout(
            self._chainForm, edit=True,
            attachForm=[(self._priorityText, 'top',    vSpc),
                        (self._up,           'left',   hSpc),
                        (self._down,         'right',  hSpc),
                        (self._add,          'left',   hSpc),
                        (self._delete,       'right',  hSpc),
                        (self._reload,       'left',   hSpc),
                        (self._reload,       'right',  hSpc),
                        (self._scrollList,   'left',   hSpc),
                        (self._scrollList,   'right',  hSpc)],
            attachControl=[(self._up,   'top', vSpc, self._priorityText),
                           (self._down, 'top', vSpc, self._priorityText),
                           (self._scrollList, 'top', vSpc, self._up),
                           (self._add,        'top', vSpc, self._scrollList),
                           (self._delete,     'top', vSpc, self._scrollList),
                           (self._reload,     'top', vSpc, self._add)])

        cmds.setParent('..')

        self._separator = cmds.separator(horizontal=False, style='singleDash')

        # Give our chained handler rules a form layout of their own, and
        # populate it with the selected rule.
        self._handlerForm = cmds.formLayout(numberOfDivisions=100)
        selectedRule = self._rulesChain[self._selectedPos]
        selectedRule.createUI()

        cmds.setParent('..')

        cmds.formLayout(
            self._form, edit=True,
            attachForm=[(self._chainForm,   'top',    0),
                        (self._chainForm,   'bottom', 0),
                        (self._chainForm,   'left',   0),
                        (self._separator,   'top',    vSpc),
                        (self._separator,   'bottom', vSpc),
                        (self._handlerForm, 'top',    0),
                        (self._handlerForm, 'bottom', 0),
                        (self._handlerForm, 'right',  0)],
            attachPosition=[(self._chainForm, 'right', hSpc, 50)],
            attachControl=[(self._separator,   'left', hSpc, self._chainForm),
                           (self._handlerForm, 'left', hSpc, self._separator)])

        cmds.setParent('..')

        # Select the default rule, which is considered by SynColor to be at
        # position 0.
        self.selectRule(0)

    def onAddRule(self, *args):

        # Obtain rule name.
        okStr = maya.stringTable['y_inputSpaceRulesUI.kColorMgtOK' ]
        cancelStr = maya.stringTable['y_inputSpaceRulesUI.kColorMgtCancel' ]

        result = cmds.promptDialog(
            title=maya.stringTable['y_inputSpaceRulesUI.kRuleDialogTitle' ],
            message=maya.stringTable['y_inputSpaceRulesUI.kRuleDialogMsg' ],
            button=[okStr, cancelStr], defaultButton=okStr,
            cancelButton=cancelStr, dismissString=cancelStr)

        if result != okStr:
            return
            
        text = cmds.promptDialog(query=True, text=True)
        
        # Create rule with match all pattern, 'exr' extension, and same color
        # space as default rule.
        rules = cmds.colorManagementFileRules(listRules=True)
        colorSpace = cmds.colorManagementFileRules(
            rules[0], query=True, colorSpace=True)

        cmds.colorManagementFileRules(add=text, pattern='*',
            extension='exr', colorSpace=colorSpace)

        self.appendRule(FilePathRule(name=text))

    def onDeleteRule(self, *args):

        # If selected rule is 0 (default), early out.
        if self._selectedPos == 0:
            return

        # Update data model.
        cmds.colorManagementFileRules(rm=self._rulesChain[self._selectedPos].name)

        del self._rulesChain[self._selectedPos]
        self._selectedPos = min(self._selectedPos, len(self._rulesChain)-1)

        self.updateScrollList()

        self.selectRule(self._selectedPos)

    def onUp(self, *args):

        # If last rule selected, early out.
        if self._selectedPos == (len(self._rulesChain)-1):
            return

        # Update data model.
        cmds.colorManagementFileRules(
            up=self._rulesChain[self._selectedPos].name)

        # Take the selected rule, move it up, and rebuild the scroll list.
        nextRule = self._rulesChain[self._selectedPos+1]

        self._rulesChain[self._selectedPos+1] = \
            self._rulesChain[self._selectedPos]

        self._rulesChain[self._selectedPos] = nextRule

        self.updateScrollList()

        self.selectRule(self._selectedPos+1)

    def onDown(self, *args):

        # Rule 0 can't be moved, and therefore rule 1 can't either.
        if self._selectedPos <= 1:
            return

        # Update data model.
        cmds.colorManagementFileRules(
            down=self._rulesChain[self._selectedPos].name)

        # Take the selected rule, move it down, and rebuild the scroll list.
        previousRule = self._rulesChain[self._selectedPos-1]

        self._rulesChain[self._selectedPos-1] = \
            self._rulesChain[self._selectedPos]

        self._rulesChain[self._selectedPos] = previousRule

        self.updateScrollList()

        self.selectRule(self._selectedPos-1)

    def onSelect(self, *args):

        # Contrary to documentation, selection queries returns a list of
        # indices (most likely because of multi-selection mode).  We use
        # single selection, so we know the list will have a single element.
        selectedRuleIndex = cmds.textScrollList(self._scrollList, query=True,
                                                selectIndexedItem=True)

        self._selectedPos = self.indexToPosition(selectedRuleIndex[0])

        self.updateHandlerRuleUI()

    def onReapply(self, *args):
        reapplyRules.reapply()

def build():
    global parentForm
    parentForm = cmds.setParent(query=True)
    createUI()
    cmds.scriptJob(event=['colorMgtConfigChanged', createUI])
    cmds.scriptJob(event=['colorMgtPrefsReloaded', createUI])
    cmds.scriptJob(event=['colorMgtOCIORulesEnabledChanged', createUI])

def createUI():
    if( not cmds.control(parentForm, exists=True) ):
        return

    oldParent = cmds.setParent(query=True)
    cmds.setParent(parentForm)

    # Clear out old UI by deleting existing children.  If no children, None
    # is returned, which is not iterable.
    children = cmds.layout(parentForm, query=True, childArray=True)
    if children:
        for child in children:
            cmds.deleteUI(child)

    # Always using a chain rule, as we always have at least two rules to
    # deal with.
    rule = ChainRule()
    rule.createUI()

    cmds.setParent(oldParent)
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
