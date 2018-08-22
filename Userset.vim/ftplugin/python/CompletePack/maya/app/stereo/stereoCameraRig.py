import sys
import maya.cmds as cmds
import maya.mel as mel

from maya.app.stereo import stereoCameraErrors
from maya.app.stereo import stereoCameraUtil 

"""
This module contains all of the code responsible for creating and querying
stereo rigs. There are four main functions provided within this module:

  - createStereoCameraRig
  - listRigs
  - leftCam
  - rightCam
  - centerCam

The function createStereoCameraRig is responsible for creating new stereo
cameras and placing them in the 3d scene.  The function listRigs lists all
of the stereo cameras in the current scene.  Finally the leftCamera and
rightCamera functions provide access to the left and right camera given a
main stereo camera (provided by listRigs).
"""

def __addAttrAndConnect(attr, node, otherNode):
	"""
	Private method to create a dynamic message attribute if it does not
	exist yet. The attribute is then connected to the one passed as
	argument.
	"""
	try:
		if cmds.attributeQuery(attr, n=node, exists=True):
			if not cmds.attributeQuery(attr, n=node, message=True):
				stereoCameraErrors.displayError('kAttributeAlreadyExists', attr, node )
				return False
		else:
			cmds.addAttr(node, longName=attr, attributeType='message' )

		# otherNode can be None for the optional rig nodes
		if otherNode <> None:
			connections = cmds.listConnections( node+'.'+attr, shapes=True,
												source=True, destination=False )
			# Keep the connection if it was set already in the rig structure.
			if (connections == None):
				cmds.connectAttr( otherNode+'.message', node+'.'+attr)
		return True
	except:
		stereoCameraErrors.displayError( 'kCannotConnect', attr, node )
	return False

def __makeTransform( dagNode ):
	if cmds.objectType(dagNode, isAType='transform'):
		return dagNode
	xform = cmds.listRelatives(dagNode, path=True, parent=True)[0]
	return xform

def __isCamera(node):
	"Return true if the argument is a camera shape, or a transform above one"
	if cmds.objectType(node, isAType='camera'):
		return True
	if not cmds.objectType(node, isAType='transform'):
		return False
	# In some custom rigs, users may have an additional transform above
	# all cameras.  We allow this connection through a proxy.  So we
	# just want to check to see if any cameras exist below this xform.
	# 
	cams = cmds.listRelatives(node, allDescendents=True, type='camera')
	if cams == None:
		return False
	if len(cams) >= 1:
		return True
	return False

def __validateRig(rigRoot, leftCam, rightCam):
	"""Make sure the 3 objects form a valid stereo rig. If the rig is
	valid, return the transforms, even if the shapes were passed in.
	If the rig is invalid, print an error message and return
	[None, None, None]
	"""
	result = [None, None, None]

	# Make sure the arguments are cameras.
	if not __isCamera(rigRoot):
		stereoCameraErrors.displayError('kNotACamera', rigRoot, 1)
		return result
	# Use the transform, if the shape was passed in
	rigRoot = __makeTransform(rigRoot)

	if not __isCamera(leftCam):
		stereoCameraErrors.displayError('kNotACamera', leftCam, 2)
		return result
	# Use the transform, if the shape was passed in
	leftCam = __makeTransform(leftCam)

	if not __isCamera(rightCam):
		stereoCameraErrors.displayError('kNotACamera', rightCam, 3)
		return result
	# Use the transform, if the shape was passed in
	rightCam = __makeTransform(rightCam)

	return [rigRoot, leftCam, rightCam]

def setStereoPair(rigRoot, leftCam, rightCam):
	"""
	Take an existing rig, and change the left and right ca
	"""
	for pair in [[leftCam, 'leftCam'],[rightCam, 'rightCam']]:
		cam  = pair[0]
		attr = pair[1]
		if not cmds.attributeQuery(attr, n=rigRoot, exists=True):
			stereoCameraErrors.displayError('kAttributeNotFound', attr, node )
		else:
			cmds.connectAttr( cam+'.message', rigRoot+'.'+attr, force=True)

def makeStereoCameraRig(rigRoot, rigTypeName, leftCam, rightCam):
	"""
	Take the root of a hiearchy, a left and right camera under that
	root, and build the attributes and connections necessary for Maya
	to consider it as a stereo rig.
	"""

	[rigRoot, leftCam, rightCam] = __validateRig(rigRoot, leftCam, rightCam)
	if  rigRoot == None:
		return

	altRig = _followProxyConnection(rigRoot)
	if len(altRig) > 0: 
		rigRoot = altRig[0] 
	
	# Mark the rig root with a special attribute. Store the rig type
	# there.
	if not cmds.attributeQuery('stereoRigType', n=rigRoot, exists=True):
		cmds.addAttr(rigRoot, longName='stereoRigType', dataType='string')
	cmds.setAttr(rigRoot+'.stereoRigType', rigTypeName, type="string")

	# Assume the root is also the center camera. For custom rigs, this
	# could be connected elsewhere.
	centerCam = rigRoot

	# Create the dynamic attributes representing the rig functions:
	__addAttrAndConnect('centerCam', rigRoot, centerCam)
	__addAttrAndConnect('leftCam',   rigRoot, leftCam)
	__addAttrAndConnect('rightCam',  rigRoot, rightCam)

def rigType( rigRoot ):
	if cmds.attributeQuery( 'stereoRigType', n=rigRoot, exists=True ):
		name = cmds.getAttr( rigRoot + '.stereoRigType' )
		return name
	return '' 


def createStereoCameraRig( rigName="" ):
	"""
	Create a stereo camera rig.
	The rig creation call back is called, then specific dynamic
	attributes are created to track cameras belonging to stereo rigs.

	If no rigName is set, the default rig tool is used.

	Return an array [rig root, Left eye camera, right eye camera]
	"""
	definitions = None
	rigRoot = None
	leftCam = ''
	rightCam = ''
	proxyObj = None 
	try:
		definitions = cmds.stereoRigManager(rigDefinition=rigName)
	except:
		stereoCameraErrors.displayError('kNoStereoRigCommand', rigName)

	try:
		# Call the creation method
		dagObjects = stereoCameraUtil.__call(definitions[0], definitions[1], rigName)
		if dagObjects <> 'Error':
			try:
				size = len(dagObjects)
				# For those users who want to create custom rigs  
				# have the proxy object selected after creation, they need to pass 
				# back a 4th parameter when the rig is created. This 4th parameter 
				# points to the actual object to be selected. 
				#  
				if size == 3 or size == 4:
					[rigRoot, leftCam, rightCam] = __validateRig(dagObjects[0], dagObjects[1], dagObjects[2])
					if size == 4:
						proxyObj = dagObjects[3]
				else:
					stereoCameraErrors.displayError('kRigReturnError', rigName, len(dagObjects))
			except:
				stereoCameraErrors.displayError('kRigReturnNotArray', rigName)

	except:
		stereoCameraErrors.displayError('kCannotCreateRig', rigName)

	if not rigRoot == None:
		rigTypeName = rigName
		if rigTypeName == "":
			rigTypeName = cmds.stereoRigManager(query=True, defaultRig=True)

		makeStereoCameraRig(rigRoot, rigTypeName, leftCam, rightCam)
		if proxyObj:
			rigRoot = proxyObj
			cmds.select( proxyObj, replace=True )
		else:
			cmds.select( rigRoot, replace=True )

	return [rigRoot, leftCam, rightCam]

def __followRootConnection(node, attr):
	"""
	Return the node connected to the specified attribte on the root
	of the rig.
	Return None for all error cases.
	"""
	root = rigRoot(node)
	if root <> '':
		connections = cmds.listConnections( root+'.'+attr, shapes=True,
											source=True, destination=False )
		if (connections <> None) and (len(connections) == 1):
			return connections[0]
	return None

def isRigRoot( dagObject ):
	"""
	Return true if this DAG object is the root of a stereo rig.
	"""
	if cmds.attributeQuery('stereoRigType', n=dagObject, exists=True):
		return True
	return False

def rigRoot( dagObject ):
	"""
	Return the root of the rig if this dagObject belongs to a stereo rig.
	Returns an empty string if the dagObject does not belong to any rig.
	"""
	if isRigRoot( dagObject ):	return dagObject
	parents = cmds.listRelatives(dagObject, path=True, parent=True )
	if parents == None:			return ''
	# we do not allow instances inside a rig
	if len(parents) <> 1:		return ''
	return rigRoot(parents[0])

def  _followProxyConnection( dagObject ):
	result = [] 
	if cmds.attributeQuery('proxyRig', n=dagObject, exists=True):
		connections = cmds.listConnections( dagObject+'.proxyRig',
											source=False, destination=True )
		if (connections <> None):
			for c in connections:
				if isRigRoot(c):
					result.append(c)
	elif isRigRoot(dagObject):
		result.append(dagObject)
	return result
		
def listRigs( rigOnly = False ):
	"""
	Lists the current stereo camera rigs in the scene. Return the list
	of root nodes.
	"""

	result = []
	
	# The expectation is that there are only a small number of cameras
	# in the scene, so collecting and testing only cameras is faster
	# than traversing all transforms.
	cameras = cmds.ls( type='camera' )
	cameraSets = []
	if not rigOnly:
		cameraSets = cmds.ls( type='cameraSet' )
	
	# We assume that the main camera is directly parented to the rig
	# root. If we want rigs to be more general, then we should call
	# rigRoot on all cameras, and remove duplicates.
	
	# Bug 348821: Checking for the case with no cams --RJ
	if (cameras == None):
		return result

	for c in cameras:
		parents = cmds.listRelatives(c, path=True, parent=True )
		if (parents <> None):
			result = result + _followProxyConnection( parents[0] )
		

	result.sort()
	cameraSets.sort()	
	return result + cameraSets


def __findCam( viewCam, attribute ):
	"Private method to find left, right, center cameras"
	cam = __followRootConnection(viewCam, attribute)
	if cam <> None:
		return cam
	stereoCameraErrors.displayError( 'kNoStereoCameraFound',
									 viewCam, attribute )

	return viewCam

def leftCam( viewCam ):
	"""
	Given the main camera node, indicate which camera is the left camera.
	If the left camera coud not be found, viewCam is returned
	"""
	return __findCam( viewCam, 'leftCam' )

def rightCam( viewCam ):
	"Same as leftCam for the right camera."
	return __findCam( viewCam, 'rightCam' )

def centerCam( viewCam ):
	"Same as leftCam for the center camera."
	return __findCam( viewCam, 'centerCam' )

def setZeroParallaxPlane( viewCam, distance ):
	center = centerCam(viewCam)
	if cmds.objExists( center + '.zeroParallax' ):
		cmds.setAttr(center + '.zeroParallax', distance )
		return

	stereoCameraErrors.displayWarning( 'kUnableToSetZeroParallax' )

def selectedCameras():
	"""
	Return the current list of selected stereo cameras in the scene.
	"""

	cameras = cmds.ls( selection=True, dag=True, type='camera' )
	transforms = cmds.ls( selection=True, dag=True, type='transform' )
	
	# We assume that the main camera is directly parented to the rig
	# root. If we want rigs to be more general, then we should call
	# rigRoot on all cameras, and remove duplicates.
	result = []
	
	for c in cameras:
		parents = cmds.listRelatives(c, path=True, parent=True)
		if (parents <> None):
			rigRoot = _followProxyConnection( parents[0] )
			if len(rigRoot) and isRigRoot(rigRoot[0]):
				result.append(rigRoot[0])
	for t in transforms:
		if isRigRoot(t):
			result.append(t)

	return result
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
