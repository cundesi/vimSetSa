import maya.cmds as cmds
from maya.app.stereo import stereoCameraSets

"""
This module defines a Stereo Camera rig.

    createRig() creates the rig itself
    registerThisRig() registers it into the system
"""

def __createSlaveCamera(masterShape, name, parent):
  """
  Private method to this module.
  Create a slave camera
  Make the default connections between the master camera and the slave one.
  """

  # First create a camera under the right parent with the desired name
  #
  slave = cmds.camera()[0]
  slave = cmds.parent(slave, parent)[0]
  slave = cmds.rename(slave, name)
  slaveShape = cmds.listRelatives(slave, path=True, shapes=True)[0]
  
  # Change some default attributes
  #
  cmds.setAttr( slave + '.renderable', 0 )
  
  # Connect the camera attributes from the master, hide them
  #
  for attr in [ 'horizontalFilmAperture',
                'verticalFilmAperture',
                'focalLength',
                'lensSqueezeRatio',
                'fStop',
                'focusDistance',
                'shutterAngle',
                'cameraPrecompTemplate',
                'filmFit',
                'displayFilmGate',
                'displayResolution',
                'nearClipPlane',
                'farClipPlane' ] :
    slaveAttr = slaveShape + '.' + attr
    cmds.connectAttr(masterShape + '.' + attr, slaveAttr)
    cmds.setAttr(slaveAttr, keyable=False )
    
  # Hide some more attributes on the transform
  #
  for attr in [ 'scaleX', 'scaleY', 'scaleZ',
                'visibility',
                'centerOfInterest' ] :
    cmds.setAttr( slave + '.' + attr, keyable=False )

  return slave

def __createFrustumNode( mainCam, parent, baseName ):
  """
  Private method to this module.
  Create a display frustum node under the given parent.
  Make the default connections between the master camera and the frustum  
  Remove some of the channel box attributes that we do not want to show
  up in the channel box. 
  """

  frustum = cmds.createNode( 'stereoRigFrustum', name=baseName, parent=parent )
  for attr in [ 'localPositionX', 'localPositionY', 'localPositionZ',
                'localScaleX', 'localScaleY', 'localScaleZ' ] :
    cmds.setAttr( frustum + '.' + attr, channelBox=False )

  for attr in ['displayNearClip', 'displayFarClip', 'displayFrustum',
               'zeroParallaxPlane',
               'zeroParallaxTransparency',
               'zeroParallaxColor',
               'safeViewingVolume',
               'safeVolumeTransparency',
               'safeVolumeColor',
               'safeStereo',
               'zeroParallax' ] :
    cmds.connectAttr( mainCam+'.'+attr, frustum+'.'+attr )
    
  return frustum

def createRig(basename='stereoCamera'):
  """
  Creates a new stereo rig. Uses a series of Maya commands to build
  a stereo rig.
  
  The optional argument basename defines the base name for each DAG
  object that will be created.
  """

  # Create the root of the rig
  # 
  root = cmds.createNode( 'stereoRigTransform', name=basename )

  # The actual basename use is the name of the top transform. If a
  # second rig is created, the default base name may be incremented
  # (e.g. stereoRig1). We want to use the same name for the whole
  # hierarchy.
  # If such a name already exists, root will be a partial path. Keep
  # only the last part for the name.
  #
  rootName = root.split('|')[-1]

  # Create the center (main) camera
  # Connect the center camera attributes to the root
  # Change any default parameters.
  #
  centerCam = cmds.createNode('stereoRigCamera',
                              name=rootName + 'CenterCamShape',
                              parent=root )
  for attr in ['stereo', 'interaxialSeparation',
               'zeroParallax', 'toeInAdjust',
               'filmOffsetRightCam', 'filmOffsetLeftCam'] :
    cmds.connectAttr( centerCam+'.'+attr, root+'.'+attr )
  cmds.connectAttr( centerCam + '.focalLength', root + '.focalLengthInput' )
  cmds.setAttr( centerCam + '.stereo', 2 )
  cmds.setAttr( centerCam + '.renderable', 0 )

  # Create the Frustum node, connect it to the root.
  #
  frustum = __createFrustumNode(centerCam, root, rootName + 'Frustum')

  # Create the left & right eye cameras
  # 
  leftCam  = __createSlaveCamera(centerCam, rootName+'Left',  root)
  rightCam = __createSlaveCamera(centerCam, rootName+'Right', root)

  # Set up message attribute connections to define the role of each camera
  #
  cmds.connectAttr( leftCam   + '.message', frustum + '.leftCamera' )
  cmds.connectAttr( rightCam  + '.message', frustum + '.rightCamera' )
  cmds.connectAttr( centerCam + '.message', frustum + '.centerCamera')

  # Connect the specific left and right output attributes of the root
  # transform to the corresponding left and right camera attributes.
  #
  cmds.connectAttr( root + '.stereoLeftOffset',  leftCam  + '.translateX')
  cmds.connectAttr( root + '.stereoRightOffset', rightCam + '.translateX')
  cmds.connectAttr( root + '.stereoLeftAngle',  leftCam  + '.rotateY' )
  cmds.connectAttr( root + '.stereoRightAngle', rightCam + '.rotateY' )
  cmds.connectAttr( root + '.filmBackOutputLeft',  leftCam  + '.hfo' )
  cmds.connectAttr( root + '.filmBackOutputRight', rightCam + '.hfo' )

  # Lock the attributes that should not be manipulated by the artist.
  #
  for attr in [ 'translate', 'rotate' ] :
    cmds.setAttr( leftCam  + '.' + attr, lock=True )
    cmds.setAttr( rightCam + '.' + attr, lock=True )

  cmds.select(root)
  
  return [root, leftCam, rightCam]

def attachToCameraSet( *args, **keywords ):
  # The camera set creation will notify after all layers have been
  # created.  It will contain the keyword allDone.  We ignore those
  # calls for now.
  #
  if not keywords.has_key( 'allDone' ):
    stereoCameraSets.parentToLayer0Rig( *args, cameraSet=keywords['cameraSet'] )

rigTypeName = 'StereoCamera'

def registerThisRig():
  """
  Registers the rig in Maya's database
  """
  global rigTypeName 
  cmds.stereoRigManager(add=[rigTypeName, 'Python',
                             'maya.app.stereo.stereoCameraDefaultRig.createRig'])
  cmds.stereoRigManager(cameraSetFunc=[rigTypeName,
                                       'maya.app.stereo.stereoCameraDefaultRig.attachToCameraSet'])
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
