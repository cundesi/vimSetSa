"""
Dialog for adjusting the background image of a container node.
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)

import maya.cmds as cmds
import maya.mel as mel
import sys

class TselectionWin(object):
    """ Base class for a dialog which works on the user's selection """
    def __init__(self, title, selectionFilter = lambda n: True, objects=[]):
        """ selectionFilter - function which returns True if object is selectable """
        self.objects = [o for o in objects if selectionFilter(o)]
        self._title = title
        self._filter = selectionFilter
        self._wnd = None

    def activate(self, window):
        """ Call this method once the window is created """
        self._wnd = window
        self.selectionChangesScriptJob = cmds.scriptJob( protected=True,
                                                         parent=window,
                                                         event=['SelectionChanged',self.onSelectionChanged] )
        # set window size
        cmds.window(self._wnd, e=True, h=176)
        cmds.window(self._wnd, e=True, w=454)

    def onSelectionChanged(self,*args):
        """ 
        Called anytime the selection list changes,
        self.objects is updated and window title is updated.
        """
        # set the window title to indicate if 1 or more objects are
        # selected
        self.objects = [ o for o in cmds.ls(selection=True, long=True) if self._filter(o)]
        cmds.window( self._wnd, edit=True, title = self.getWindowTitle( ) )

    def getWindowTitle(self):
        windowTitle = self._title + ': '
        suffix = maya.stringTable['y_adjustBackgroundImageWin.kNothingIsSelected']
        if len(self.objects):
            suffix = self.objects[0]
            if len(self.objects) > 1:
                suffix += r"..."
        windowTitle += suffix
        return windowTitle

    def __del__(self):
        self.close()

    def close(self):
        if self._wnd: 
            cmds.deleteUI( self._wnd, window=True )
        
class TadjustBackgroundImageWin( TselectionWin ):
    """ Adjust the background image for a container Dialog """
    def __init__(self, editor):

        def selectionFilter( obj ):
            return cmds.container(obj, q=True, isContainer=True)

        self.useFeedback = False
        selectedNodes = [ o for o in cmds.ls(selection=True,long=True) if selectionFilter(o) ]
        TselectionWin.__init__(self, 
                               maya.stringTable['y_adjustBackgroundImageWin.kAttributeWndTitle'], 
                               selectionFilter, selectedNodes )
        self.editor = editor

    def hyperGraphCmd(self, *args, **kwargs):
        if self.useFeedback:
            kwargs['useFeedbackList'] = True
        return cmds.hyperGraph( *args, **kwargs )
            
    def onSelectionChanged(self,*args):
        """ override selection callback """
        self.useFeedback = False
        TselectionWin.onSelectionChanged( self, args )
        self.update()

    def loadImage( self, theFile ):
        if theFile:
            self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                                image=theFile )
            self.update()

    def onLoadImage(self):
        # browse to image file
        try:
            imageFolder = cmds.workspace(expandName=cmds.workspace('images', q=True, fileRuleEntry=True))
            filter = mel.eval('buildPixmapFileFilterList()');
            theFile = cmds.fileDialog2( fileMode=1,
                                        okCaption=maya.stringTable['y_adjustBackgroundImageWin.kLoad'],
                                        caption=maya.stringTable['y_adjustBackgroundImageWin.kLoadImage' ], 
                                        fileFilter=filter,
                                        startingDirectory=imageFolder
                                        );
            self.loadImage(theFile[0])
        except (TypeError,IndexError):
            pass
        except RuntimeError,ex:
            cmds.error(unicode(ex))

    def onImageFieldChange(self, val):
        if len(self.objects):
            self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                                image=val )
            self.update()

    def onAdjustImagePositionHorizontal(self, val):
        if len(self.objects):
            curPos = self.hyperGraphCmd( self.editor, q=True, imageForContainer=True,
                                      imagePosition=True )
            if curPos and len(curPos) > 1:
                posX = float(val)
                posY = curPos[1]
                self.hyperGraphCmd( self.editor, e=True, imageForContainer=True,
                                 imagePosition=(posX,posY) )

    def onAdjustImagePositionVertical(self,val):
        if len(self.objects):
            curPos = self.hyperGraphCmd( self.editor, q=True, imageForContainer=True,
                                      imagePosition=True )
            if curPos and len(curPos) > 1:
                posY = float(val)
                posX = curPos[0]
                self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                                 imagePosition=(posX,posY) )

    def onAdjustImageScale(self, val):
        if len(self.objects):
            fval = float(val)
            if ( fval > 0):
                self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                                 imageScale=fval )
                self.hyperGraphCmd( self.editor, e=True, forceRefresh=True )
        
    def onFitToWidth(self, arg):
        if len(self.objects):
            self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                             fitImageToWidth=True )
            self.update()
            self.hyperGraphCmd( self.editor, e=True, forceRefresh=True )
        
    def onFitToHeight(self, arg):
        if len(self.objects):
            self.hyperGraphCmd( self.editor, e=True, imageForContainer=True, 
                             fitImageToHeight=True )
            self.update()
            self.hyperGraphCmd( self.editor, e=True, forceRefresh=True )

    def show(self):
        """ Build and show the dialog """
        windowTitle = self.getWindowTitle( )

        wnd = cmds.window( resizeToFitChildren=True,
                           title= windowTitle, 
                           minimizeButton=False,
                           maximizeButton=False,
                           retain=False )
        # build widgets
        topFormLayout = cmds.formLayout()
        topColumnLayout = cmds.columnLayout( rowSpacing=10 )

        self.imageNameField = cmds.textFieldButtonGrp( 
            label= maya.stringTable['y_adjustBackgroundImageWin.kImageName' ],
            fileName= "",
            editable= True,
            buttonLabel= maya.stringTable['y_adjustBackgroundImageWin.kLoad2' ],
            buttonCommand= self.onLoadImage,
            changeCommand = self.onImageFieldChange)
        self.adjustImageHPositionSlider = cmds.floatSliderGrp(
            label= maya.stringTable['y_adjustBackgroundImageWin.kHorizontalPosition' ],
            field= True,
            min= 0,
            max= 1000.0,
            precision= 2,
            value= 0,
            dragCommand = self.onAdjustImagePositionHorizontal,
            changeCommand= self.onAdjustImagePositionHorizontal )
        self.adjustImageVPositionSlider = cmds.floatSliderGrp(
            label= maya.stringTable['y_adjustBackgroundImageWin.kVerticalPosition' ],
            field= True,
            min= 0,
            max= 1000.0,
            precision= 2,
            value= 0,
            dragCommand = self.onAdjustImagePositionVertical,
            changeCommand =self.onAdjustImagePositionVertical )
        self.adjustImageScaleSlider = cmds.floatSliderGrp(
            label= maya.stringTable['y_adjustBackgroundImageWin.kScale' ],
            field= True,
            min= 0.1,
            max= 10.0,
            fieldMaxValue= 1000.0,
            precision= 2,
            value=0,
            dragCommand = self.onAdjustImageScale,
            changeCommand = self.onAdjustImageScale )

        cmds.setParent( upLevel=True )

	adjustImageFitToWidthButton = cmds.button(
            label = maya.stringTable['y_adjustBackgroundImageWin.kFitToWidth' ],
            command = self.onFitToWidth )

	adjustImageFitToHeightButton = cmds.button(
            label= maya.stringTable['y_adjustBackgroundImageWin.kFitToHeight' ],
            command= self.onFitToHeight )

	cmds.formLayout( topFormLayout, edit=True,
                         attachForm = [	(topColumnLayout,	'left',	5),
                                        (topColumnLayout,	'top',	5),
                                        (topColumnLayout,	'right',5),
                                        (adjustImageFitToWidthButton, 'left',5),
                                        (adjustImageFitToHeightButton, 'right',5)],
                         attachNone = [	(adjustImageFitToHeightButton,'bottom'),
                                        (topColumnLayout,	'bottom'),
                                        (adjustImageFitToWidthButton,'bottom')],
                         attachControl =[ (adjustImageFitToWidthButton,	'top',	10,topColumnLayout),
                                          (adjustImageFitToHeightButton,'left',5,adjustImageFitToWidthButton),
                                          (adjustImageFitToHeightButton,'top',10,topColumnLayout)],
                         attachPosition = [(adjustImageFitToWidthButton,'right',5,50)] )

	self.update() 
        self.activate( wnd )
        cmds.showWindow( wnd )

    def update(self):
        """ update the ui after something has changed """
        if len(self.objects):
            imageName = self.hyperGraphCmd(self.editor, query=True,imageForContainer=True,image=True)
            cmds.textFieldButtonGrp( self.imageNameField, edit=True, enable=True, fileName=imageName )

            imagePosition = self.hyperGraphCmd(self.editor, query=True,imageForContainer=True,imagePosition=True)
            cmds.floatSliderGrp( self.adjustImageHPositionSlider, edit=True, enable=True, value = imagePosition[0] )
            cmds.floatSliderGrp( self.adjustImageVPositionSlider, edit=True, enable=True, value = imagePosition[1] )

            imageScaling = self.hyperGraphCmd(self.editor, query=True,imageForContainer=True,imageScale=True)
            cmds.floatSliderGrp( self.adjustImageScaleSlider, edit=True, enable=True, value = imageScaling )
        else:
            # no containers selected, disable controls
            cmds.control( self.imageNameField, edit = True, enable = False )
            cmds.control( self.adjustImageHPositionSlider, edit = True, enable = False )
            cmds.control( self.adjustImageVPositionSlider, edit = True, enable = False )
            cmds.control( self.adjustImageScaleSlider, edit = True, enable = False )

def adjustBackgroundImageWin( editor ):
    """
    Main entry point.  Create and show the adjust-background-image dialog.
    """
    dlg = TadjustBackgroundImageWin( editor )
    dlg.show()
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
